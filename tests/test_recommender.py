"""
RRVDXB Backend — tests/test_recommender.py
Unit tests for the recommender maths (Day 10).

The verifier scripts test the API end to end. These test the algorithms in
isolation, against tiny handcrafted datasets where the correct answer can be
worked out by hand — so a regression points at the exact function that broke
rather than "some channel changed".

Run:
    pytest -q

Owner: Ubaid Ullah Farooqui (UF)
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from app.ai.embeddings import build_content_neighbours, build_tfidf, cosine, tokenize
from app.ai.recommender import RecommenderService
from app.services.recommender_data import Basket, Dataset, Interaction, Product

NOW = datetime.now(timezone.utc)


def product(pid: int, name: str, stock: int = 10, available: bool = True, **kw) -> Product:
    return Product(
        id=pid,
        name=name,
        description=kw.get("description", ""),
        price=kw.get("price", 100.0),
        category_name=kw.get("category_name", "Electronics"),
        brand_name=kw.get("brand_name", "TestBrand"),
        stock=stock,
        is_available=available,
        average_rating=kw.get("average_rating", 4.0),
    )


def basket(user_id: int, ids: list[int], days_ago: int = 1) -> Basket:
    return Basket(user_id, ids, NOW - timedelta(days=days_ago))


def interaction(user_id: int, pid: int, source: str = "order", days_ago: int = 1) -> Interaction:
    weights = {"order": 1.0, "cart": 0.6, "wishlist": 0.5, "review": 0.4}
    return Interaction(user_id, pid, source, weights[source], NOW - timedelta(days=days_ago))


@pytest.fixture
def service() -> RecommenderService:
    return RecommenderService()


# ---------------------------------------------------------------------------
# Co-occurrence maths
# ---------------------------------------------------------------------------


def test_cooccurrence_uses_cosine_normalisation(service):
    """
    Three products. Product 1 appears in 4 baskets, 2 in three of them, 3 in one.

      count(1)=4  count(2)=3  count(3)=1
      pair(1,2)=3 -> 3 / sqrt(4*3) = 0.866
      pair(1,3)=1 -> 1 / sqrt(4*1) = 0.500

    Raw counts would say 2 is three times as related to 1 as 3 is. Normalised,
    the gap narrows to the truth: 2 is *more* related, but 3 co-occurs every
    single time it is bought, so it is not dismissed.
    """
    dataset = Dataset(
        "test",
        products=[product(1, "Phone"), product(2, "Earbuds"), product(3, "Case")],
        baskets=[
            basket(1, [1, 2]),
            basket(2, [1, 2]),
            basket(3, [1, 2]),
            basket(4, [1, 3]),
        ],
    )
    index = service._build_index(dataset)
    scores = dict(index.cooccurrence[1])

    assert scores[2] == pytest.approx(3 / math.sqrt(4 * 3), abs=1e-6)
    assert scores[3] == pytest.approx(1 / math.sqrt(4 * 1), abs=1e-6)
    assert scores[2] > scores[3]


def test_bestseller_does_not_dominate_everything(service):
    """
    A product in every basket must not come out as the closest neighbour of
    every other product. This is the failure mode raw co-occurrence counts
    have, and the reason for the sqrt denominator.
    """
    bestseller = 99
    dataset = Dataset(
        "test",
        products=[product(i, f"Item {i}") for i in (1, 2, 3, 4, bestseller)],
        baskets=[
            basket(1, [1, 2, bestseller]),
            basket(2, [1, 2, bestseller]),
            basket(3, [3, 4, bestseller]),
            basket(4, [3, 4, bestseller]),
        ],
    )
    index = service._build_index(dataset)

    # Item 1's closest neighbour should be item 2 (always bought together),
    # not the bestseller that is simply in every basket.
    assert index.cooccurrence[1][0][0] == 2


def test_similarity_is_symmetric_and_self_free(service):
    dataset = Dataset(
        "test",
        products=[product(i, f"Item {i}") for i in (1, 2, 3)],
        baskets=[basket(1, [1, 2, 3]), basket(2, [1, 2])],
    )
    index = service._build_index(dataset)

    for pid, neighbours in index.cooccurrence.items():
        assert pid not in dict(neighbours), "a product is its own neighbour"
        for other, score in neighbours:
            assert dict(index.cooccurrence[other])[pid] == pytest.approx(score)


def test_empty_dataset_builds_without_crashing(service):
    index = service._build_index(Dataset("empty"))
    assert index.cooccurrence == {}
    assert index.profiles == {}


# ---------------------------------------------------------------------------
# User profiles and recency decay
# ---------------------------------------------------------------------------


def test_recent_interactions_outweigh_old_ones(service):
    """A 30-day half-life means yesterday's signal is worth ~2x last month's."""
    dataset = Dataset(
        "test",
        products=[product(1, "A"), product(2, "B")],
        interactions=[
            interaction(7, 1, "order", days_ago=0),
            interaction(7, 2, "order", days_ago=30),
        ],
    )
    index = service._build_index(dataset)
    profile = index.profiles[7]

    assert profile[1] > profile[2]
    assert profile[2] == pytest.approx(profile[1] * 0.5, rel=0.05)


def test_order_signal_outweighs_wishlist(service):
    dataset = Dataset(
        "test",
        products=[product(1, "A"), product(2, "B")],
        interactions=[
            interaction(7, 1, "order", days_ago=0),
            interaction(7, 2, "wishlist", days_ago=0),
        ],
    )
    profile = service._build_index(dataset).profiles[7]
    assert profile[1] > profile[2]


def test_last_purchase_tracks_the_most_recent_order(service):
    dataset = Dataset(
        "test",
        products=[product(1, "A"), product(2, "B")],
        interactions=[
            interaction(7, 1, "order", days_ago=10),
            interaction(7, 2, "order", days_ago=2),
        ],
    )
    assert service._build_index(dataset).last_purchase[7] == 2


# ---------------------------------------------------------------------------
# Eligibility
# ---------------------------------------------------------------------------


def test_out_of_stock_and_unavailable_are_never_recommended(service):
    dataset = Dataset(
        "test",
        products=[
            product(1, "In stock"),
            product(2, "Out of stock", stock=0),
            product(3, "Withdrawn", available=False),
        ],
        baskets=[basket(1, [1, 2, 3]), basket(2, [1, 2, 3])],
        interactions=[interaction(7, 1)],
    )
    service._dataset = dataset
    service._index = service._build_index(dataset)
    service._loaded_at = float("inf")  # keep warmup from reloading

    payload = service.recommend(user_id=7, limit=10)
    surfaced = {
        item["productId"] for channel in payload.values() for item in channel
    }
    assert "P002" not in surfaced
    assert "P003" not in surfaced


def test_owned_products_are_excluded_from_personalized(service):
    dataset = Dataset(
        "test",
        products=[product(i, f"Item {i}") for i in (1, 2, 3)],
        baskets=[basket(1, [1, 2]), basket(2, [1, 2]), basket(3, [2, 3])],
        interactions=[interaction(7, 1, "order"), interaction(7, 2, "cart")],
    )
    service._dataset = dataset
    service._index = service._build_index(dataset)
    service._loaded_at = float("inf")

    personalized = service.personalized(dataset, 7, 10)
    assert "P001" not in {i["productId"] for i in personalized}
    assert "P002" not in {i["productId"] for i in personalized}


def test_limit_is_clamped_to_configured_maximum(service):
    dataset = Dataset(
        "test",
        products=[product(i, f"Item {i}") for i in range(1, 41)],
        baskets=[basket(1, list(range(1, 41)))],
    )
    service._dataset = dataset
    service._index = service._build_index(dataset)
    service._loaded_at = float("inf")

    payload = service.recommend(user_id=None, limit=9999)
    assert all(len(channel) <= 20 for channel in payload.values())


def test_guest_still_gets_every_channel(service):
    dataset = Dataset(
        "test",
        products=[product(i, f"Item {i}") for i in (1, 2, 3)],
        baskets=[basket(1, [1, 2])],
    )
    service._dataset = dataset
    service._index = service._build_index(dataset)
    service._loaded_at = float("inf")

    payload = service.recommend(user_id=None, limit=3)
    assert all(payload[c] for c in ("personalized", "trending", "boughtTogether"))


def test_product_id_formatting():
    service = RecommenderService()
    assert service.format_product_id(1) == "P001"
    assert service.format_product_id(42) == "P042"
    assert service.format_product_id(1234) == "P1234"


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------


def test_tokenize_drops_stopwords_and_single_characters():
    assert tokenize("The best of a Phone X") == ["best", "phone"]


def test_tfidf_vectors_are_l2_normalised():
    vectors = build_tfidf({1: "wireless bluetooth speaker", 2: "leather travel bag"})
    for vector in vectors.values():
        assert math.sqrt(sum(v * v for v in vector.values())) == pytest.approx(1.0)


def test_cosine_bounds():
    vectors = build_tfidf({1: "wireless speaker", 2: "wireless speaker", 3: "leather bag"})
    assert cosine(vectors[1], vectors[2]) == pytest.approx(1.0, abs=1e-6)
    assert cosine(vectors[1], vectors[3]) == pytest.approx(0.0, abs=1e-6)


def test_content_neighbours_rank_the_related_product_first():
    neighbours = build_content_neighbours(
        {
            1: "Sony wireless bluetooth headphones audio",
            2: "Sony wireless bluetooth speaker audio",
            3: "leather ladies handbag fashion",
        }
    )
    assert neighbours[1][0][0] == 2
    assert 3 not in dict(neighbours[1])


def test_empty_documents_do_not_crash():
    assert build_tfidf({}) == {}
    assert build_content_neighbours({1: ""}) == {1: []}
