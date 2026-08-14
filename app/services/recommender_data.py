"""
RRVDXB Backend — app/services/recommender_data.py
Data access for the AI Product Recommender.

Named recommender_data rather than ai_service because app/services/ai_service.py
is already taken by the sentiment module.

Reads from Talha's PostgreSQL schema when DATABASE_URL is reachable, and falls
back to the synthetic dataset (app/utils/seed_recommender_data.py) when it is not,
so this module is never blocked by the shared backend.

Tables used: products, orders (items JSONB), cart, wishlist, reviews.
Recommender data block owner: Ubaid Ullah Farooqui (UF) — Day 08
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.config import settings
from app.utils.constants import (
    RECOMMENDER_SOURCE_EMPTY,
    RECOMMENDER_SOURCE_POSTGRES,
    RECOMMENDER_SOURCE_SYNTHETIC,
    RECOMMENDER_SOURCE_WEIGHTS as SOURCE_WEIGHTS,
)

logger = logging.getLogger("rrvdxb.ai.service")


# ---------------------------------------------------------------------------
# Domain objects
# ---------------------------------------------------------------------------


@dataclass
class Product:
    id: int
    name: str
    description: str = ""
    price: float = 0.0
    category_id: int | None = None
    brand_id: int | None = None
    category_name: str = ""
    brand_name: str = ""
    stock: int = 0
    is_featured: bool = False
    is_best_seller: bool = False
    is_available: bool = True
    average_rating: float = 0.0

    @property
    def in_stock(self) -> bool:
        return self.is_available and self.stock > 0

    @property
    def text_blob(self) -> str:
        """Used for product embeddings on Day 09."""
        return " ".join(
            [self.name, self.description, self.category_name, self.brand_name]
        ).strip()


@dataclass
class Basket:
    """One order = one basket of product ids. Drives co-occurrence on Day 09."""

    user_id: int
    product_ids: list[int]
    created_at: datetime


@dataclass
class Interaction:
    """A signal that a user touched a product: order, cart, wishlist or review."""

    user_id: int
    product_id: int
    source: str
    weight: float
    created_at: datetime


@dataclass
class Dataset:
    source: str
    products: list[Product] = field(default_factory=list)
    baskets: list[Basket] = field(default_factory=list)
    interactions: list[Interaction] = field(default_factory=list)

    def products_by_id(self) -> dict[int, Product]:
        return {p.id: p for p in self.products}

    def interactions_for(self, user_id: int) -> list[Interaction]:
        return [i for i in self.interactions if i.user_id == user_id]


# ---------------------------------------------------------------------------
# PostgreSQL source
# ---------------------------------------------------------------------------


def _parse_order_items(raw) -> list[int]:
    """orders.items is JSONB. Accept a few shapes so we survive schema drift."""
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            return []
    if isinstance(raw, dict):
        raw = raw.get("items", [])
    ids: list[int] = []
    for item in raw or []:
        if isinstance(item, dict):
            value = (
                item.get("product_id")
                or item.get("productId")
                or item.get("id")
                or item.get("productID")
            )
        else:
            value = item
        try:
            ids.append(int(str(value).lstrip("Pp") or 0))
        except (TypeError, ValueError):
            continue
    return [i for i in ids if i > 0]


def load_from_postgres() -> Dataset | None:
    if not settings.DATABASE_URL:
        return None

    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        logger.warning("SQLAlchemy not installed — skipping PostgreSQL source")
        return None

    try:
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            products: list[Product] = []
            rows = conn.execute(
                text(
                    """
                    SELECT p.id, p.name, COALESCE(p.description, '') AS description,
                           COALESCE(p.price, 0) AS price, p.category_id, p.brand_id,
                           COALESCE(c.name, '') AS category_name,
                           COALESCE(b.name, '') AS brand_name,
                           COALESCE(p.stock, 0) AS stock,
                           COALESCE(p.is_featured, false) AS is_featured,
                           COALESCE(p.is_best_seller, false) AS is_best_seller,
                           COALESCE(p.is_available, true) AS is_available,
                           COALESCE(p.average_rating, 0) AS average_rating
                    FROM products p
                    LEFT JOIN categories c ON c.id = p.category_id
                    LEFT JOIN brands b ON b.id = p.brand_id
                    """
                )
            ).mappings()
            for r in rows:
                products.append(
                    Product(
                        id=r["id"],
                        name=r["name"],
                        description=r["description"],
                        price=float(r["price"]),
                        category_id=r["category_id"],
                        brand_id=r["brand_id"],
                        category_name=r["category_name"],
                        brand_name=r["brand_name"],
                        stock=r["stock"],
                        is_featured=r["is_featured"],
                        is_best_seller=r["is_best_seller"],
                        is_available=r["is_available"],
                        average_rating=float(r["average_rating"]),
                    )
                )

            baskets: list[Basket] = []
            interactions: list[Interaction] = []

            order_rows = conn.execute(
                text("SELECT user_id, items, created_at FROM orders")
            ).mappings()
            for r in order_rows:
                ids = _parse_order_items(r["items"])
                if not ids:
                    continue
                created = r["created_at"] or datetime.now(timezone.utc)
                baskets.append(Basket(r["user_id"], ids, created))
                for pid in ids:
                    interactions.append(
                        Interaction(r["user_id"], pid, "order", SOURCE_WEIGHTS["order"], created)
                    )

            for table, source in (("cart", "cart"), ("wishlist", "wishlist")):
                time_col = "added_at" if table == "cart" else "created_at"
                try:
                    rows = conn.execute(
                        text(
                            f"SELECT user_id, product_id, {time_col} AS ts FROM {table}"
                        )
                    ).mappings()
                    for r in rows:
                        interactions.append(
                            Interaction(
                                r["user_id"],
                                r["product_id"],
                                source,
                                SOURCE_WEIGHTS[source],
                                r["ts"] or datetime.now(timezone.utc),
                            )
                        )
                except Exception as exc:  # table may not exist yet
                    logger.info("Skipping %s: %s", table, exc)

        if not products:
            logger.warning("PostgreSQL reachable but products table is empty")
            return None

        logger.info(
            "Loaded from PostgreSQL: %d products, %d orders", len(products), len(baskets)
        )
        return Dataset(RECOMMENDER_SOURCE_POSTGRES, products, baskets, interactions)

    except Exception as exc:
        logger.warning("PostgreSQL unavailable (%s) — using fallback", exc)
        return None


# ---------------------------------------------------------------------------
# Synthetic source
# ---------------------------------------------------------------------------


def load_from_synthetic() -> Dataset | None:
    path = Path(settings.SYNTHETIC_DATASET_PATH)
    if not path.exists():
        logger.error(
            "Synthetic dataset missing at %s — run: python -m app.utils.seed_recommender_data",
            path,
        )
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))

    products = [Product(**p) for p in payload.get("products", [])]
    baskets = [
        Basket(
            b["user_id"],
            b["product_ids"],
            datetime.fromisoformat(b["created_at"]),
        )
        for b in payload.get("baskets", [])
    ]
    interactions = [
        Interaction(
            i["user_id"],
            i["product_id"],
            i["source"],
            SOURCE_WEIGHTS.get(i["source"], 0.5),
            datetime.fromisoformat(i["created_at"]),
        )
        for i in payload.get("interactions", [])
    ]

    logger.info(
        "Loaded synthetic dataset: %d products, %d orders", len(products), len(baskets)
    )
    return Dataset(RECOMMENDER_SOURCE_SYNTHETIC, products, baskets, interactions)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def load_dataset() -> Dataset:
    """PostgreSQL first, synthetic second, empty dataset last. Never raises."""
    dataset = load_from_postgres()
    if dataset is None and settings.USE_SYNTHETIC_FALLBACK:
        dataset = load_from_synthetic()
    return dataset or Dataset(RECOMMENDER_SOURCE_EMPTY)


def recent_cutoff(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)
