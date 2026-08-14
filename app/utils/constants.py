from typing import Final

DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100
MIN_PASSWORD_LENGTH: Final[int] = 8
MAX_NAME_LENGTH: Final[int] = 255
MAX_DESCRIPTION_LENGTH: Final[int] = 1000

ROLE_ADMIN: Final[str] = "admin"
ROLE_USER: Final[str] = "user"
ROLE_SELLER: Final[str] = "seller"

ORDER_STATUSES: Final[tuple[str, ...]] = (
    "pending",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
)

PAYMENT_STATUSES: Final[tuple[str, ...]] = (
    "pending",
    "paid",
    "failed",
    "refunded",
)

SUPPORTED_CURRENCIES: Final[tuple[str, ...]] = ("USD", "AED")
DEFAULT_CURRENCY: Final[str] = "USD"
# ===========================================================================
# AI PRODUCT RECOMMENDER — Ubaid Ullah Farooqui (UF)
# Append-only block. Every name is RECOMMENDER_-prefixed so nothing above
# is shadowed. Do not edit constants outside this block.
# ===========================================================================

# A signal that a shopper ordered a product says more than one they wishlisted.
RECOMMENDER_SOURCE_WEIGHTS: Final[dict[str, float]] = {
    "order": 1.0,
    "cart": 0.6,
    "wishlist": 0.5,
    "review": 0.4,
}

# Recency multiplier applied to orders inside TRENDING_WINDOW_DAYS.
RECOMMENDER_RECENCY_BOOST: Final[float] = 2.0

# Interest halves every N days, so last month's browsing does not outrank
# yesterday's.
RECOMMENDER_PROFILE_HALF_LIFE_DAYS: Final[float] = 30.0

# How many neighbours to keep per product when precomputing at warmup.
RECOMMENDER_COOCCURRENCE_NEIGHBOURS: Final[int] = 20
RECOMMENDER_CONTENT_NEIGHBOURS: Final[int] = 10

# Reason templates, filled from the signal that produced the suggestion.
RECOMMENDER_TEMPLATE_YOU_BOUGHT: Final[str] = "Because you bought {anchor}"
RECOMMENDER_TEMPLATE_OFTEN_WITH: Final[str] = "Often bought with {anchor}"
RECOMMENDER_TEMPLATE_SIMILAR_TO: Final[str] = "Similar to {anchor}"
RECOMMENDER_REASON_TRENDING_CATEGORY: Final[str] = "Trending in {category}"

# Fallback reasons, used when no specific signal is available.
RECOMMENDER_REASON_HISTORY: Final[str] = "Based on your browsing history"
RECOMMENDER_REASON_COLD_START: Final[str] = "Popular with shoppers like you"
RECOMMENDER_REASON_TRENDING: Final[str] = "Trending this week"
RECOMMENDER_REASON_BOUGHT_TOGETHER: Final[str] = "Frequently bought together"

# Data source labels reported by /api/ai/recommendations/health
RECOMMENDER_SOURCE_POSTGRES: Final[str] = "postgres"
RECOMMENDER_SOURCE_SYNTHETIC: Final[str] = "synthetic"
RECOMMENDER_SOURCE_EMPTY: Final[str] = "empty"
