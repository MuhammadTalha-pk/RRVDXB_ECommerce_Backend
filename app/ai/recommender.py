"""
RRVDXB Backend — app/ai/recommender.py
AI Product Recommender. Serves GET /api/ai/recommendations

Day 09 — the three channels now run three different algorithms:

  personalized    item-based collaborative filtering over the user-item matrix
                  (orders + cart + wishlist, recency-decayed)
  boughtTogether  normalised item co-occurrence from orders.items
  trending        recency-weighted purchase counts

Cold start falls through to TF-IDF content similarity (app/ai/embeddings.py),
then trending, then featured — so a channel is never empty.

Everything expensive is precomputed once at warmup into a RecommenderIndex.
A request is dictionary lookups, not matrix maths.

The API contract is unchanged from Day 08.
Owner: Ubaid Ullah Farooqui (UF)
"""

from __future__ import annotations

import logging
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import combinations

from app.ai.embeddings import build_content_neighbours
from app.core.config import settings as app_settings
from app.services.recommender_data import (
    Dataset,
    Product,
    load_dataset,
    recent_cutoff,
)
from app.utils.constants import (
    RECOMMENDER_CONTENT_NEIGHBOURS as CONTENT_NEIGHBOURS,
    RECOMMENDER_COOCCURRENCE_NEIGHBOURS as COOCCURRENCE_NEIGHBOURS,
    RECOMMENDER_PROFILE_HALF_LIFE_DAYS as PROFILE_HALF_LIFE_DAYS,
    RECOMMENDER_REASON_BOUGHT_TOGETHER as REASON_BOUGHT_TOGETHER,
    RECOMMENDER_REASON_COLD_START as REASON_COLD_START,
    RECOMMENDER_REASON_HISTORY as REASON_HISTORY,
    RECOMMENDER_REASON_TRENDING as REASON_TRENDING,
    RECOMMENDER_REASON_TRENDING_CATEGORY as REASON_TRENDING_CATEGORY,
    RECOMMENDER_RECENCY_BOOST as RECENCY_BOOST,
    RECOMMENDER_TEMPLATE_OFTEN_WITH as TEMPLATE_OFTEN_WITH,
    RECOMMENDER_TEMPLATE_SIMILAR_TO as TEMPLATE_SIMILAR_TO,
    RECOMMENDER_TEMPLATE_YOU_BOUGHT as TEMPLATE_YOU_BOUGHT,
)

logger = logging.getLogger("rrvdxb.recommender")


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@dataclass
class RecommenderIndex:
    """Everything precomputed at warmup. Requests only read from this."""

    cooccurrence: dict[int, list[tuple[int, float]]] = field(default_factory=dict)
    content: dict[int, list[tuple[int, float]]] = field(default_factory=dict)
    profiles: dict[int, dict[int, float]] = field(default_factory=dict)
    last_purchase: dict[int, int] = field(default_factory=dict)
    popularity: dict[int, float] = field(default_factory=dict)
    build_ms: float = 0.0


class RecommenderService:
    """Singleton service. Data and index are built once and refreshed on a TTL."""

    def __init__(self) -> None:
        self._settings = app_settings
        self._dataset: Dataset | None = None
        self._index: RecommenderIndex = RecommenderIndex()
        self._loaded_at: float = 0.0

    # ------------------------------------------------------------ warmup

    def warmup(self, force: bool = False) -> Dataset:
        ttl = self._settings.RECOMMENDER_CACHE_TTL_SECONDS
        expired = (time.time() - self._loaded_at) > ttl
        if force or self._dataset is None or expired:
            started = time.perf_counter()
            self._dataset = load_dataset()
            self._index = self._build_index(self._dataset)
            self._loaded_at = time.time()
            logger.info(
                "Recommender warmed from '%s' in %.0f ms "
                "(%d co-occurrence entries, %d content entries, %d user profiles)",
                self._dataset.source,
                (time.perf_counter() - started) * 1000,
                len(self._index.cooccurrence),
                len(self._index.content),
                len(self._index.profiles),
            )
        return self._dataset

    def _build_index(self, dataset: Dataset) -> RecommenderIndex:
        started = time.perf_counter()
        index = RecommenderIndex()
        if not dataset.products:
            return index

        # -- item co-occurrence from real baskets --------------------------
        pair_counts: dict[tuple[int, int], float] = defaultdict(float)
        item_counts: dict[int, float] = defaultdict(float)
        cutoff = recent_cutoff(self._settings.TRENDING_WINDOW_DAYS)

        for basket in dataset.baskets:
            ids = sorted(set(basket.product_ids))
            recent = _aware(basket.created_at) >= cutoff
            for pid in ids:
                item_counts[pid] += 1.0
                index.popularity[pid] = index.popularity.get(pid, 0.0) + (
                    RECENCY_BOOST if recent else 1.0
                )
            for left, right in combinations(ids, 2):
                pair_counts[(left, right)] += 1.0

        # Cosine normalisation: co_ij / sqrt(count_i * count_j). Without it a
        # bestseller looks "related" to everything simply by being frequent.
        similarity: dict[int, dict[int, float]] = defaultdict(dict)
        for (left, right), count in pair_counts.items():
            denominator = math.sqrt(item_counts[left] * item_counts[right]) or 1.0
            score = count / denominator
            similarity[left][right] = score
            similarity[right][left] = score

        index.cooccurrence = {
            pid: sorted(neighbours.items(), key=lambda pair: pair[1], reverse=True)[
                :COOCCURRENCE_NEIGHBOURS
            ]
            for pid, neighbours in similarity.items()
        }

        # -- rating nudge so ties break on quality -------------------------
        for product in dataset.products:
            if product.id in index.popularity:
                index.popularity[product.id] += product.average_rating * 0.1

        # -- user profiles, recency-decayed --------------------------------
        now = datetime.now(timezone.utc)
        profiles: dict[int, dict[int, float]] = defaultdict(lambda: defaultdict(float))
        latest_order_at: dict[int, datetime] = {}

        for interaction in dataset.interactions:
            age_days = max((now - _aware(interaction.created_at)).days, 0)
            decay = 0.5 ** (age_days / PROFILE_HALF_LIFE_DAYS)
            profiles[interaction.user_id][interaction.product_id] += (
                interaction.weight * decay
            )
            if interaction.source == "order":
                when = _aware(interaction.created_at)
                seen = latest_order_at.get(interaction.user_id)
                if seen is None or when > seen:
                    latest_order_at[interaction.user_id] = when
                    index.last_purchase[interaction.user_id] = interaction.product_id

        index.profiles = {uid: dict(items) for uid, items in profiles.items()}

        # -- content embeddings for cold start -----------------------------
        index.content = build_content_neighbours(
            {p.id: p.text_blob for p in dataset.products},
            top_k=CONTENT_NEIGHBOURS,
        )

        index.build_ms = (time.perf_counter() - started) * 1000
        return index

    @property
    def cache_age_seconds(self) -> float:
        return 0.0 if not self._loaded_at else time.time() - self._loaded_at

    # ------------------------------------------------------------ helpers

    def format_product_id(self, product_id: int) -> str:
        s = self._settings
        return f"{s.PRODUCT_ID_PREFIX}{int(product_id):0{s.PRODUCT_ID_PAD}d}"

    def _eligible(self, dataset: Dataset, product_id: int, exclude: set[int]) -> bool:
        product = dataset.products_by_id().get(product_id)
        return bool(product and product.in_stock and product_id not in exclude)

    def _user_owned(self, dataset: Dataset, user_id: int | None) -> set[int]:
        """Products already ordered or sitting in the cart — never re-recommend."""
        if user_id is None:
            return set()
        return {
            i.product_id
            for i in dataset.interactions_for(user_id)
            if i.source in ("order", "cart")
        }

    def _name_of(self, dataset: Dataset, product_id: int) -> str:
        product = dataset.products_by_id().get(product_id)
        return product.name if product else "your recent order"

    def _pack(self, scored: list[tuple[int, str]], limit: int) -> list[dict[str, str]]:
        return [
            {"productId": self.format_product_id(pid), "reason": reason}
            for pid, reason in scored[:limit]
        ]

    def _rank_by_popularity(
        self, dataset: Dataset, exclude: set[int], limit: int
    ) -> list[Product]:
        candidates = [p for p in dataset.products if p.in_stock and p.id not in exclude]
        candidates.sort(
            key=lambda p: (
                self._index.popularity.get(p.id, 0.0),
                p.is_best_seller,
                p.is_featured,
                p.average_rating,
            ),
            reverse=True,
        )
        return candidates[:limit]

    def _featured_fallback(
        self, dataset: Dataset, exclude: set[int], limit: int
    ) -> list[Product]:
        candidates = [p for p in dataset.products if p.in_stock and p.id not in exclude]
        candidates.sort(
            key=lambda p: (p.is_featured, p.is_best_seller, p.average_rating),
            reverse=True,
        )
        return candidates[:limit]

    # ---------------------------------------------------------- channels

    def personalized(
        self, dataset: Dataset, user_id: int | None, limit: int
    ) -> list[dict[str, str]]:
        """Item-based collaborative filtering over the shopper's own signal."""
        owned = self._user_owned(dataset, user_id)
        profile = self._index.profiles.get(user_id, {}) if user_id else {}

        scores: dict[int, float] = defaultdict(float)
        anchors: dict[int, tuple[int, float]] = {}

        for source_id, weight in profile.items():
            for neighbour_id, similarity in self._index.cooccurrence.get(source_id, []):
                if not self._eligible(dataset, neighbour_id, owned):
                    continue
                contribution = weight * similarity
                scores[neighbour_id] += contribution
                best = anchors.get(neighbour_id)
                if best is None or contribution > best[1]:
                    anchors[neighbour_id] = (source_id, contribution)

        if scores:
            ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
            return self._pack(
                [
                    (
                        pid,
                        TEMPLATE_YOU_BOUGHT.format(
                            anchor=self._name_of(dataset, anchors[pid][0])
                        ),
                    )
                    for pid, _ in ranked
                ],
                limit,
            )

        # Cold start: content similarity to whatever the shopper has touched.
        if profile:
            content_scores: dict[int, float] = defaultdict(float)
            content_anchor: dict[int, int] = {}
            for source_id, weight in profile.items():
                for neighbour_id, similarity in self._index.content.get(source_id, []):
                    if not self._eligible(dataset, neighbour_id, owned):
                        continue
                    content_scores[neighbour_id] += weight * similarity
                    content_anchor.setdefault(neighbour_id, source_id)
            if content_scores:
                ranked = sorted(
                    content_scores.items(), key=lambda pair: pair[1], reverse=True
                )
                return self._pack(
                    [
                        (
                            pid,
                            TEMPLATE_SIMILAR_TO.format(
                                anchor=self._name_of(dataset, content_anchor[pid])
                            ),
                        )
                        for pid, _ in ranked
                    ],
                    limit,
                )

        # No signal at all — guest, or a brand new account.
        picks = self._rank_by_popularity(
            dataset, owned, limit
        ) or self._featured_fallback(dataset, set(), limit)
        reason = REASON_HISTORY if profile else REASON_COLD_START
        return self._pack([(p.id, reason) for p in picks], limit)

    def trending(self, dataset: Dataset, limit: int) -> list[dict[str, str]]:
        picks = self._rank_by_popularity(dataset, set(), limit)
        if not picks:
            picks = self._featured_fallback(dataset, set(), limit)
            return self._pack([(p.id, REASON_TRENDING) for p in picks], limit)
        return self._pack(
            [
                (
                    p.id,
                    REASON_TRENDING_CATEGORY.format(category=p.category_name)
                    if p.category_name
                    else REASON_TRENDING,
                )
                for p in picks
            ],
            limit,
        )

    def bought_together(
        self, dataset: Dataset, user_id: int | None, limit: int
    ) -> list[dict[str, str]]:
        """Co-purchase neighbours of the shopper's most recent order."""
        owned = self._user_owned(dataset, user_id)
        anchor = self._index.last_purchase.get(user_id) if user_id else None

        if anchor is None:
            # Guest: anchor on the single most popular in-stock product.
            top = self._rank_by_popularity(dataset, set(), 1)
            anchor = top[0].id if top else None

        if anchor is not None:
            anchor_name = self._name_of(dataset, anchor)
            neighbours = [
                (pid, TEMPLATE_OFTEN_WITH.format(anchor=anchor_name))
                for pid, _ in self._index.cooccurrence.get(anchor, [])
                if self._eligible(dataset, pid, owned | {anchor})
            ]
            if neighbours:
                return self._pack(neighbours, limit)

            # Anchor has no co-purchase history yet — use content similarity.
            content = [
                (pid, TEMPLATE_SIMILAR_TO.format(anchor=anchor_name))
                for pid, _ in self._index.content.get(anchor, [])
                if self._eligible(dataset, pid, owned | {anchor})
            ]
            if content:
                return self._pack(content, limit)

        picks = self._rank_by_popularity(
            dataset, owned, limit
        ) or self._featured_fallback(dataset, set(), limit)
        return self._pack([(p.id, REASON_BOUGHT_TOGETHER) for p in picks], limit)

    # ------------------------------------------------------------- public

    def recommend(self, user_id: int | None, limit: int | None = None) -> dict:
        settings = self._settings
        limit = limit or settings.RECOMMENDER_DEFAULT_LIMIT
        limit = max(1, min(limit, settings.RECOMMENDER_MAX_LIMIT))

        started = time.perf_counter()
        dataset = self.warmup()

        payload = {
            "personalized": self.personalized(dataset, user_id, limit),
            "trending": self.trending(dataset, limit),
            "boughtTogether": self.bought_together(dataset, user_id, limit),
        }

        logger.info(
            "recommend(user=%s, limit=%d) source=%s in %.1f ms",
            user_id,
            limit,
            dataset.source,
            (time.perf_counter() - started) * 1000,
        )
        return payload

    def health(self) -> dict:
        dataset = self.warmup()
        return {
            "status": "ok" if dataset.products else "degraded",
            "source": dataset.source,
            "productsLoaded": len(dataset.products),
            "ordersLoaded": len(dataset.baskets),
            "cacheAgeSeconds": round(self.cache_age_seconds, 1),
        }


recommender_service = RecommenderService()
