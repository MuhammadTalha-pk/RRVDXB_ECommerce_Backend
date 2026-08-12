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
