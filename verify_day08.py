"""
RRVDXB Backend — verify_day08.py
Day 08 acceptance checks for the AI Product Recommender.

Run from the project root with the venv active:
    python verify_day08.py

Exits 0 if everything passes, 1 if anything fails.
Owner: Ubaid Ullah Farooqui (UF)
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

BASE_DIR = Path(__file__).resolve().parent
ENDPOINT = "/api/ai/recommendations"
CHANNELS = ("personalized", "trending", "boughtTogether")

results: list[tuple[bool, str, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((condition, name, detail))
    mark = "PASS" if condition else "FAIL"
    line = f"[{mark}] {name}"
    if detail:
        line += f"  ->  {detail}"
    print(line)


def main() -> int:
    print("=" * 72)
    print("RRVDXB — AI Product Recommender · Day 08 acceptance checks")
    print("=" * 72)

    with TestClient(app) as client:
        # -- 1. endpoint is reachable ------------------------------------
        r = client.get(f"{ENDPOINT}?userId=7&limit=5")
        check("Endpoint returns 200", r.status_code == 200, f"status {r.status_code}")
        if r.status_code != 200:
            return 1
        body = r.json()

        # -- 2. contract shape -------------------------------------------
        check(
            "Response has exactly the three contract keys",
            set(body.keys()) == set(CHANNELS),
            f"keys: {sorted(body.keys())}",
        )

        shape_ok = True
        for channel in CHANNELS:
            for item in body.get(channel, []):
                if set(item.keys()) != {"productId", "reason"}:
                    shape_ok = False
        check(
            "Every item is exactly {productId, reason}",
            shape_ok,
            "camelCase contract intact",
        )

        id_ok = all(
            re.fullmatch(r"P\d{3,}", item["productId"])
            for channel in CHANNELS
            for item in body[channel]
        )
        check("productId matches the P001 format", id_ok)

        reasons_ok = all(
            isinstance(item["reason"], str) and item["reason"].strip()
            for channel in CHANNELS
            for item in body[channel]
        )
        check("Every item carries a non-empty reason string", reasons_ok)

        # -- 3. no empty channels (AI checklist: fallback responses) -----
        empties = [c for c in CHANNELS if not body[c]]
        check("No channel is empty for a known user", not empties, f"empty: {empties}")

        # -- 4. limit honoured -------------------------------------------
        r3 = client.get(f"{ENDPOINT}?userId=7&limit=3").json()
        check(
            "limit=3 returns at most 3 per channel",
            all(len(r3[c]) <= 3 for c in CHANNELS),
            {c: len(r3[c]) for c in CHANNELS},
        )

        over = client.get(f"{ENDPOINT}?userId=7&limit=999")
        check("limit=999 rejected with 422", over.status_code == 422, f"status {over.status_code}")

        bad = client.get(f"{ENDPOINT}?userId=0")
        check("userId=0 rejected with 422", bad.status_code == 422, f"status {bad.status_code}")

        # -- 5. fallback chain -------------------------------------------
        guest = client.get(ENDPOINT)
        guest_ok = guest.status_code == 200 and all(guest.json()[c] for c in CHANNELS)
        check("Guest request (no userId) still returns products", guest_ok)

        unknown = client.get(f"{ENDPOINT}?userId=999999")
        unknown_ok = unknown.status_code == 200 and all(unknown.json()[c] for c in CHANNELS)
        check("Unknown userId falls back instead of failing", unknown_ok)

        # -- 6. eligibility filtering ------------------------------------
        from app.ai.recommender import recommender_service

        dataset = recommender_service.warmup()
        blocked = {
            recommender_service.format_product_id(p.id)
            for p in dataset.products
            if not p.in_stock
        }
        wide = client.get(f"{ENDPOINT}?limit=20").json()
        surfaced = {i["productId"] for c in CHANNELS for i in wide[c]}
        leaked = blocked & surfaced
        check(
            "Out-of-stock / unavailable products excluded",
            not leaked,
            f"{len(blocked)} blocked, leaked: {sorted(leaked) or 'none'}",
        )

        # -- 7. no re-recommending what the shopper already has ----------
        target = next(
            (
                i.user_id
                for i in dataset.interactions
                if i.source in ("order", "cart")
            ),
            None,
        )
        if target is not None:
            owned = {
                recommender_service.format_product_id(pid)
                for pid in recommender_service._user_owned(dataset, target)
            }
            personal = {
                i["productId"] for i in client.get(f"{ENDPOINT}?userId={target}&limit=10").json()["personalized"]
            }
            check(
                "Already ordered / in-cart items not re-recommended",
                not (owned & personal),
                f"user {target}, owns {len(owned)} products",
            )

        # -- 8. NFR-02 latency budget ------------------------------------
        timings = []
        for _ in range(20):
            t0 = time.perf_counter()
            client.get(f"{ENDPOINT}?userId=7&limit=5")
            timings.append((time.perf_counter() - t0) * 1000)
        worst = max(timings)
        check(
            "AI response under 4s (NFR-02)",
            worst < 4000,
            f"worst of 20 requests: {worst:.1f} ms",
        )

        # -- 9. health + refresh -----------------------------------------
        health = client.get(f"{ENDPOINT}/health")
        hb = health.json()
        check(
            "Health endpoint reports a live data source",
            health.status_code == 200 and hb["productsLoaded"] > 0,
            f"source={hb.get('source')}, products={hb.get('productsLoaded')}, orders={hb.get('ordersLoaded')}",
        )
        refresh = client.post(f"{ENDPOINT}/refresh")
        check("Refresh endpoint works", refresh.status_code == 200)

        # -- 10. stability -----------------------------------------------
        codes = {client.get(f"{ENDPOINT}?userId={u}").status_code for u in range(1, 51)}
        check("50 consecutive users all return 200", codes == {200}, f"codes seen: {codes}")

    # -- 11. secrets hygiene (NFR-04) -------------------------------------
    leaked_files = []
    for path in (BASE_DIR / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"gsk_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}", text):
            leaked_files.append(str(path.relative_to(BASE_DIR)))
    check("No hardcoded API keys in app/", not leaked_files, str(leaked_files or "clean"))

    gitignore = BASE_DIR / ".gitignore"
    check(
        ".env is gitignored",
        gitignore.exists() and ".env" in gitignore.read_text(encoding="utf-8"),
    )
    check("`.env.example` present for the team", (BASE_DIR / ".env.example").exists())

    # -- summary -----------------------------------------------------------
    passed = sum(1 for ok, _, _ in results if ok)
    total = len(results)
    print("=" * 72)
    print(f"{passed}/{total} checks passed")
    failed = [name for ok, name, _ in results if not ok]
    if failed:
        print("\nFailed:")
        for name in failed:
            print(f"  - {name}")
        print("\nDay 08 is NOT ready to submit.")
        return 1
    print("\nDay 08 verified. Safe to package and submit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
