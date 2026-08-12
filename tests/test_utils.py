from decimal import Decimal

from app.utils.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    ORDER_STATUSES,
    PAYMENT_STATUSES,
    ROLE_ADMIN,
    ROLE_USER,
)
from app.utils.helpers import (
    format_currency,
    generate_order_number,
    generate_slug,
    normalize_text,
)
from app.utils.validators import (
    validate_email,
    validate_password,
    validate_phone,
    validate_price,
)


def test_generate_slug_and_normalize_text():
    assert generate_slug("Premium Shoes") == "premium-shoes"
    assert normalize_text("  Hello   WORLD  ") == "hello world"


def test_format_currency_and_order_number():
    assert format_currency(Decimal("19.99")) == "$19.99"
    assert generate_order_number("user")
    assert generate_order_number("user").startswith("user-")


def test_validation_helpers():
    assert validate_email("user@example.com") is True
    assert validate_email("invalid") is False
    assert validate_password("StrongPass1!") is True
    assert validate_password("weak") is False
    assert validate_phone("+971501234567") is True
    assert validate_phone("123") is False
    assert validate_price(Decimal("10.50")) is True
    assert validate_price(Decimal("-1")) is False


def test_constants_values():
    assert DEFAULT_PAGE_SIZE == 20
    assert MAX_PAGE_SIZE == 100
    assert ROLE_ADMIN == "admin"
    assert ROLE_USER == "user"
    assert ORDER_STATUSES[0] == "pending"
    assert PAYMENT_STATUSES[0] == "pending"
