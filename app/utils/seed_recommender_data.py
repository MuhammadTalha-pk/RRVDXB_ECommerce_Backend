"""
RRVDXB Backend — app/utils/seed_recommender_data.py
Synthetic dataset generator for the AI recommender.

There will be almost no real order data before the demo, and collaborative
filtering on an empty user-item matrix returns nothing. This builds a realistic
catalogue with deliberate co-purchase bundles so the Day 09 algorithms have a
signal to find and the demo is never empty.

Run:  python -m app.utils.seed_recommender_data
Out:  data/synthetic_dataset.json

Owner: Ubaid Ullah Farooqui (UF) — Day 08
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT = BASE_DIR / "data" / "synthetic_dataset.json"

RANDOM_SEED = 42
USER_COUNT = 200
ORDER_COUNT = 600

random.seed(RANDOM_SEED)

CATEGORIES = {1: "Electronics", 2: "Fashion", 3: "Perfumes", 4: "Accessories"}
BRANDS = {1: "Apple", 2: "Sony", 3: "Adidas", 4: "Lacoste", 5: "Chanel", 6: "RRVDXB"}

# (name, category_id, brand_id, price AED, description)
CATALOGUE = [
    ("iPhone 14 Pro Max", 1, 1, 4299.0, "Flagship smartphone with ProMotion display"),
    ("iPhone AirPods Pro", 1, 1, 899.0, "Active noise cancelling wireless earbuds"),
    ("Apple Watch Series 9", 1, 1, 1499.0, "Fitness and health smartwatch"),
    ("MagSafe Charger", 1, 1, 199.0, "Fast wireless charger for iPhone"),
    ("iPhone Silicone Case", 4, 1, 129.0, "Protective slim case for iPhone"),
    ("PlayStation 5 Console", 1, 2, 2299.0, "Next generation gaming console"),
    ("PlayStation 5 Joystick", 1, 2, 349.0, "DualSense wireless controller"),
    ("Sony WH-1000XM5 Headphones", 1, 2, 1399.0, "Over-ear noise cancelling headphones"),
    ("Sony Bluetooth Speaker", 1, 2, 449.0, "Portable waterproof audio speaker"),
    ("Sony 4K Smart TV 55", 1, 2, 2799.0, "Ultra HD LED smart television"),
    ("Adidas Ultraboost Sneakers", 2, 3, 649.0, "Running sneakers with boost cushioning"),
    ("Adidas Track Jacket", 2, 3, 379.0, "Classic three stripe sports jacket"),
    ("Adidas Sports Socks Pack", 2, 3, 79.0, "Breathable cotton socks three pack"),
    ("Lacoste Polo Shirt", 2, 4, 429.0, "Pique cotton polo with crocodile logo"),
    ("Lacoste Leather Belt", 4, 4, 289.0, "Reversible leather belt for men"),
    ("Lacoste Sport Perfume", 3, 4, 319.0, "Fresh citrus fragrance for men"),
    ("Chanel No 5 Perfume", 3, 5, 749.0, "Iconic floral aldehyde fragrance"),
    ("Chanel Ladies Handbag", 4, 5, 3299.0, "Quilted leather shoulder handbag"),
    ("Chanel Sunglasses", 4, 5, 1099.0, "Oversized UV protection sunglasses"),
    ("Silver Earrings", 4, 6, 149.0, "Sterling silver drop earrings"),
    ("Silver Pendant Necklace", 4, 6, 219.0, "Minimal sterling silver pendant"),
    ("Harak Perfume", 3, 6, 259.0, "Oriental oud fragrance unisex"),
    ("Body Spray Musk", 3, 6, 59.0, "Long lasting daily body spray"),
    ("Ladies Stiletto Heels", 2, 6, 389.0, "Pointed toe evening stilettos"),
    ("Ladies Tote Handbag", 4, 6, 469.0, "Spacious everyday leather tote"),
    ("Men's Formal Shoes", 2, 6, 549.0, "Genuine leather oxford shoes"),
    ("Smart Fitness Band", 1, 6, 179.0, "Heart rate and sleep tracking band"),
    ("Power Bank 20000mAh", 1, 6, 149.0, "Fast charge dual port power bank"),
    ("Wireless Gaming Mouse", 1, 2, 229.0, "Low latency ergonomic gaming mouse"),
    ("Travel Backpack", 4, 6, 299.0, "Water resistant laptop travel backpack"),
]

# Deliberate co-purchase bundles (1-indexed positions in CATALOGUE).
BUNDLES = [
    [1, 2, 4, 5],        # iPhone + AirPods + charger + case
    [6, 7, 29],          # PS5 + joystick + gaming mouse
    [8, 9, 28],          # headphones + speaker + power bank
    [11, 12, 13],        # Adidas sneakers + jacket + socks
    [14, 15, 16],        # Lacoste polo + belt + perfume
    [17, 18, 19],        # Chanel perfume + handbag + sunglasses
    [20, 21, 22],        # silver earrings + necklace + Harak perfume
    [24, 25, 23],        # heels + tote + body spray
    [26, 15, 30],        # formal shoes + belt + backpack
    [3, 27, 28],         # watch + fitness band + power bank
]


def build_products() -> list[dict]:
    products = []
    for idx, (name, category_id, brand_id, price, description) in enumerate(
        CATALOGUE, start=1
    ):
        products.append(
            {
                "id": idx,
                "name": name,
                "description": description,
                "price": price,
                "category_id": category_id,
                "brand_id": brand_id,
                "category_name": CATEGORIES[category_id],
                "brand_name": BRANDS[brand_id],
                "stock": random.choice([0, 3, 8, 15, 25, 40, 60]),
                "is_featured": idx in (2, 20, 22),
                "is_best_seller": idx in (1, 7, 18, 23),
                "is_available": True,
                "average_rating": round(random.uniform(3.4, 4.9), 2),
            }
        )
    # A couple of out-of-stock items so the eligibility filter gets exercised.
    products[12]["stock"] = 0
    products[18]["is_available"] = False
    return products


def build_orders(product_count: int) -> tuple[list[dict], list[dict]]:
    baskets: list[dict] = []
    interactions: list[dict] = []
    now = datetime.now(timezone.utc)

    for _ in range(ORDER_COUNT):
        user_id = random.randint(1, USER_COUNT)
        days_ago = random.choices(
            population=[random.randint(0, 6), random.randint(7, 60)],
            weights=[0.35, 0.65],
        )[0]
        created = now - timedelta(days=days_ago, hours=random.randint(0, 23))

        bundle = random.choice(BUNDLES)
        picked = random.sample(bundle, k=random.randint(2, len(bundle)))
        if random.random() < 0.3:  # occasional unrelated add-on
            picked.append(random.randint(1, product_count))
        picked = sorted(set(picked))

        baskets.append(
            {
                "user_id": user_id,
                "product_ids": picked,
                "created_at": created.isoformat(),
            }
        )
        for pid in picked:
            interactions.append(
                {
                    "user_id": user_id,
                    "product_id": pid,
                    "source": "order",
                    "created_at": created.isoformat(),
                }
            )

    # Cart and wishlist signals for users who have not ordered much.
    for _ in range(400):
        user_id = random.randint(1, USER_COUNT)
        created = now - timedelta(days=random.randint(0, 30))
        interactions.append(
            {
                "user_id": user_id,
                "product_id": random.randint(1, product_count),
                "source": random.choice(["cart", "wishlist", "review"]),
                "created_at": created.isoformat(),
            }
        )

    return baskets, interactions


def main() -> None:
    products = build_products()
    baskets, interactions = build_orders(len(products))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": RANDOM_SEED,
        "products": products,
        "baskets": baskets,
        "interactions": interactions,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote {OUTPUT}")
    print(f"  products     : {len(products)}")
    print(f"  orders       : {len(baskets)}")
    print(f"  interactions : {len(interactions)}")
    print(f"  users        : {USER_COUNT}")


if __name__ == "__main__":
    main()
