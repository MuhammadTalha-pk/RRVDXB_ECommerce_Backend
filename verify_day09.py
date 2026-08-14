"""
RRVDXB Backend — verify_day09.py
Day 09 acceptance checks for the AI Product Recommender.

Day 08 proved the contract. This proves the algorithms behind it are real:
the three channels must now disagree with each other, and the co-occurrence
matrix must recover the bundles that exist in the data.

Run from the project root with the venv active:
    python verify_day09.py

Exits 0 if everything passes, 1 if anything fails.
Owner: Ubaid Ullah Farooqui (UF)
"""

from __future__ import annotations

import sys
import time

from fastapi.testclient import TestClient

from app.ai.recommender import recommender_service
from app.main import app

ENDPOINT = "/api/ai/recommendations"
CHANNELS = ("personalized", "trending", "boughtTogether")

results: list[tuple[bool, str, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((condition, name, detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f"  ->  {detail}" if detail else ""))


def ids(payload: dict, channel: str) -> list[str]:
    return [item["productId"] for item in payload[channel]]


def main() -> int:
    print("=" * 72)
    print("RRVDXB — AI Product Recommender · Day 09 acceptance checks")
    print("=" * 72)

    with TestClient(app) as client:
        dataset = recommender_service.warmup()
        index = recommender_service._index

        # -- 1. the index actually got built ------------------------------
        check(
            "Co-occurrence matrix built from orders",
            len(index.cooccurrence) > 0,
            f"{len(index.cooccurrence)} products have co-purchase neighbours",
        )
        check(
            "Content embeddings built for every product",
            len(index.content) == len(dataset.products),
            f"{len(index.content)} / {len(dataset.products)} products embedded",
        )
        check(
            "User profiles built from interactions",
            len(index.profiles) > 0,
            f"{len(index.profiles)} shoppers profiled",
        )
        check(
            "Index build stays fast",
            index.build_ms < 2000,
            f"{index.build_ms:.0f} ms",
        )

        # -- 2. similarity is symmetric and self-free ---------------------
        asymmetric = 0
        self_referential = 0
        lookup = {pid: dict(pairs) for pid, pairs in index.cooccurrence.items()}
        for pid, neighbours in lookup.items():
            if pid in neighbours:
                self_referential += 1
            for other, score in neighbours.items():
                back = lookup.get(other, {}).get(pid)
                if back is not None and abs(back - score) > 1e-9:
                    asymmetric += 1
        check("Similarity matrix is symmetric", asymmetric == 0, f"{asymmetric} mismatches")
        check("No product is its own neighbour", self_referential == 0)

        # -- 3. co-occurrence recovers the real bundles -------------------
        # The seed data pairs the iPhone (P001) with AirPods / charger / case.
        # If normalisation is right, those outrank unrelated bestsellers.
        iphone_neighbours = [pid for pid, _ in index.cooccurrence.get(1, [])[:3]]
        check(
            "Co-occurrence recovers the iPhone bundle",
            bool({2, 4, 5} & set(iphone_neighbours)),
            f"top neighbours of P001: {iphone_neighbours}",
        )

        ps5_neighbours = [pid for pid, _ in index.cooccurrence.get(6, [])[:3]]
        check(
            "Co-occurrence recovers the PS5 bundle",
            bool({7, 29} & set(ps5_neighbours)),
            f"top neighbours of P006: {ps5_neighbours}",
        )

        # -- 4. the three channels now disagree ---------------------------
        target = next(iter(index.last_purchase), None)
        payload = client.get(f"{ENDPOINT}?userId={target}&limit=5").json()
        personal, trend, together = (ids(payload, c) for c in CHANNELS)

        check(
            "personalized differs from trending",
            personal != trend,
            f"{personal} vs {trend}",
        )
        check(
            "boughtTogether differs from trending",
            together != trend,
            f"{together} vs {trend}",
        )

        # -- 5. recommendations are actually personal ---------------------
        sampled = list(index.profiles.keys())[:25]
        distinct = {tuple(ids(client.get(f"{ENDPOINT}?userId={u}&limit=5").json(), "personalized")) for u in sampled}
        check(
            "Different shoppers get different suggestions",
            len(distinct) > 1,
            f"{len(distinct)} distinct result sets across {len(sampled)} shoppers",
        )

        # -- 6. reasons are derived from signal, not hardcoded ------------
        product_names = {p.name for p in dataset.products}
        specific = [
            item["reason"]
            for channel in ("personalized", "boughtTogether")
            for item in payload[channel]
            if any(name in item["reason"] for name in product_names)
        ]
        check(
            "Reasons name the product that triggered them",
            len(specific) > 0,
            f"e.g. {specific[0] if specific else 'none'}",
        )
        categories = {p.category_name for p in dataset.products if p.category_name}
        trend_specific = [
            item["reason"]
            for item in payload["trending"]
            if any(c in item["reason"] for c in categories)
        ]
        check(
            "Trending reasons name the category",
            len(trend_specific) > 0,
            f"e.g. {trend_specific[0] if trend_specific else 'none'}",
        )

        # -- 7. boughtTogether anchors on the shopper's last purchase -----
        anchor_id = index.last_purchase.get(target)
        anchor_name = next(
            (p.name for p in dataset.products if p.id == anchor_id), ""
        )
        anchored = [
            item for item in payload["boughtTogether"] if anchor_name in item["reason"]
        ]
        check(
            "boughtTogether anchors on the last order",
            bool(anchored),
            f"anchor: {anchor_name}",
        )
        check(
            "Anchor product is not recommended back",
            recommender_service.format_product_id(anchor_id) not in together,
        )

        # -- 8. cold start still works ------------------------------------
        guest = client.get(f"{ENDPOINT}?limit=5").json()
        check(
            "Guest gets all three channels populated",
            all(guest[c] for c in CHANNELS),
        )
        unknown = client.get(f"{ENDPOINT}?userId=999999&limit=5").json()
        check(
            "Unknown shopper falls back cleanly",
            all(unknown[c] for c in CHANNELS),
        )

        # -- 9. still inside the latency budget ---------------------------
        timings = []
        for user in range(1, 101):
            start = time.perf_counter()
            client.get(f"{ENDPOINT}?userId={user}&limit=5")
            timings.append((time.perf_counter() - start) * 1000)
        worst = max(timings)
        check(
            "AI response under 4s across 100 shoppers (NFR-02)",
            worst < 4000,
            f"worst {worst:.1f} ms, mean {sum(timings)/len(timings):.1f} ms",
        )

        # -- 10. no stock leakage through the new paths -------------------
        blocked = {
            recommender_service.format_product_id(p.id)
            for p in dataset.products
            if not p.in_stock
        }
        leaked = set()
        for user in list(index.profiles.keys())[:50]:
            body = client.get(f"{ENDPOINT}?userId={user}&limit=20").json()
            leaked |= blocked & {i["productId"] for c in CHANNELS for i in body[c]}
        check(
            "Out-of-stock never leaks through CF or content paths",
            not leaked,
            f"leaked: {sorted(leaked) or 'none'}",
        )

    passed = sum(1 for ok, _, _ in results if ok)
    print("=" * 72)
    print(f"{passed}/{len(results)} checks passed")
    failed = [name for ok, name, _ in results if not ok]
    if failed:
        print("\nFailed:")
        for name in failed:
            print(f"  - {name}")
        print("\nDay 09 is NOT ready to submit.")
        return 1
    print("\nDay 09 verified. Run verify_day08.py too — the contract must still hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
