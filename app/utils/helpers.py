import re
import uuid
from decimal import Decimal
from typing import Any

from app.utils.constants import DEFAULT_CURRENCY, SUPPORTED_CURRENCIES


def normalize_text(value: str) -> str:
    """Normalize whitespace and casing for display or search usage."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip().lower()


def generate_slug(value: str, fallback: str | None = None) -> str:
    """Create a URL-safe slug from a human-readable string."""
    if not value:
        return fallback or "item"
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_text(value)).strip("-")
    return slug or fallback or "item"


def format_currency(amount: Decimal | float | int, currency: str = DEFAULT_CURRENCY) -> str:
    """Format a monetary value using a consistent currency representation."""
    normalized_currency = currency.upper()
    if normalized_currency not in SUPPORTED_CURRENCIES:
        normalized_currency = DEFAULT_CURRENCY

    normalized = Decimal(str(amount)).quantize(Decimal("0.01"))
    if normalized_currency == "USD":
        return f"${normalized:.2f}"
    if normalized_currency == "AED":
        return f"د.إ{normalized:.2f}"
    return f"{normalized:.2f}"


def generate_order_number(prefix: str = "ORD") -> str:
    """Create a short unique order identifier."""
    suffix = str(uuid.uuid4().hex)[:8].upper()
    return f"{prefix}-{suffix}"


def safe_get(mapping: dict[str, Any], key: str, default: Any = None) -> Any:
    """Return a dictionary value without raising if the mapping is missing."""
    if not isinstance(mapping, dict):
        return default
    return mapping.get(key, default)
