import re
from decimal import Decimal
from typing import Any

from app.utils.constants import MIN_PASSWORD_LENGTH


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9\s-]{7,15}$")


def validate_email(value: str) -> bool:
    """Validate a basic email address format."""
    return bool(value and EMAIL_PATTERN.match(value.strip()))


def validate_password(value: str) -> bool:
    """Ensure the password has enough complexity for application use."""
    if not isinstance(value, str) or len(value) < MIN_PASSWORD_LENGTH:
        return False
    return any(char.isdigit() for char in value) and any(char.isalpha() for char in value)


def validate_phone(value: str) -> bool:
    """Validate a simple international or local phone number."""
    return bool(value and PHONE_PATTERN.match(value.strip()))


def validate_price(value: Any) -> bool:
    """Ensure the value is a positive decimal price."""
    try:
        amount = Decimal(str(value))
    except (TypeError, ValueError, ArithmeticError):
        return False
    return amount > 0


def validate_required_string(value: Any, field_name: str = "value") -> str:
    """Check that a required string field contains usable data."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    return cleaned
