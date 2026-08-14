from __future__ import annotations

from typing import Any, Mapping


class PricePredictorService:
    """Lightweight price forecasting service for product cards and carts."""

    CATEGORY_MULTIPLIERS = {
        "electronics": 1.08,
        "fashion": 1.05,
        "perfumes": 1.12,
        "accessories": 1.04,
        "home": 1.03,
        "beauty": 1.07,
        "default": 1.0,
    }

    BRAND_PREMIUMS = {
        "apple": 1.12,
        "sony": 1.08,
        "chanel": 1.18,
        "lacoste": 1.09,
        "adidas": 1.07,
        "harak": 1.1,
        "default": 1.0,
    }

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @classmethod
    def _product_snapshot(cls, product: Mapping[str, Any]) -> dict[str, Any]:
        current_price = cls._to_float(product.get("price") or product.get("current_price"), 0.0)
        stock = int(product.get("stock", 20) or 20)
        rating = cls._to_float(product.get("average_rating") or product.get("rating") or 3.8, 3.8)
        category = str(product.get("category") or "default").strip().lower()
        brand = str(product.get("brand") or "default").strip().lower()
        currency = str(product.get("currency") or "AED").upper()
        name = str(product.get("name") or "Product")
        return {
            "name": name,
            "base_price": current_price,
            "stock": stock,
            "rating": max(1.0, min(5.0, rating)),
            "category": category,
            "brand": brand,
            "currency": currency,
        }

    def predict(self, product: Mapping[str, Any] | Any) -> dict[str, Any]:
        if product is None:
            raise ValueError("Product payload is required")

        if not isinstance(product, Mapping):
            product = product.__dict__ if hasattr(product, "__dict__") else {}

        snapshot = self._product_snapshot(product)
        base_price = snapshot["base_price"]

        if base_price <= 0:
            return {
                "success": False,
                "currency": snapshot["currency"],
                "predicted_price": 0.0,
                "current_price": 0.0,
                "change_percent": 0.0,
                "confidence": 0.0,
                "summary": "Price prediction unavailable because the product price is missing or invalid.",
                "trend": "unknown",
                "product_name": snapshot["name"],
            }

        category_mult = self.CATEGORY_MULTIPLIERS.get(snapshot["category"], self.CATEGORY_MULTIPLIERS["default"])
        brand_mult = self.BRAND_PREMIUMS.get(snapshot["brand"], self.BRAND_PREMIUMS["default"])

        stock_pressure = 1.0 + max(0.0, (20 - snapshot["stock"])) * 0.006
        rating_adjustment = 1.0 + (snapshot["rating"] - 3.8) * 0.04
        seasonality = 1.0 + (0.03 if snapshot["category"] == "perfumes" else 0.0)

        predicted = base_price * category_mult * brand_mult * stock_pressure * rating_adjustment * seasonality
        predicted = round(predicted, 2)

        change_percent = round(((predicted - base_price) / base_price) * 100, 2) if base_price else 0.0
        confidence = round(max(0.55, min(0.96, 0.7 + (snapshot["rating"] - 3.0) * 0.08)), 2)

        if change_percent > 0:
            trend = "upward"
        elif change_percent < 0:
            trend = "downward"
        else:
            trend = "stable"

        summary = (
            f"Based on category demand, {snapshot['name']}'s market value is projected at "
            f"{snapshot['currency']} {predicted:,.2f}, a {abs(change_percent):.2f}% {trend} change from the current price."
        )

        return {
            "success": True,
            "currency": snapshot["currency"],
            "current_price": round(base_price, 2),
            "predicted_price": predicted,
            "change_percent": change_percent,
            "confidence": confidence,
            "summary": summary,
            "trend": trend,
            "product_name": snapshot["name"],
        }


price_predictor_service = PricePredictorService()
