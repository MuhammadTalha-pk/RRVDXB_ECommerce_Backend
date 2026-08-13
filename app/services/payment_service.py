import logging
from decimal import Decimal
from typing import Any, Mapping

import stripe

from app.core.config import settings

logger = logging.getLogger(__name__)


class PaymentService:
    """Centralized payment logic for Stripe-backed or mock payment flows."""

    def __init__(self) -> None:
        self.stripe_api_key = settings.STRIPE_API_KEY
        self.default_currency = "aed"

    def _normalize_amount(self, amount: int | float | Decimal | str) -> int:
        if amount is None:
            raise ValueError("Payment amount is required.")

        try:
            normalized = Decimal(str(amount))
        except Exception as exc:  # pragma: no cover - defensive validation
            raise ValueError("Invalid payment amount.") from exc

        if normalized <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        cents = (normalized * Decimal("100")).to_integral_value()
        if cents != normalized * Decimal("100"):
            raise ValueError("Payment amount must be expressed in major currency units with at most 2 decimal places.")

        return int(cents)

    def create_payment_intent(
        self,
        amount: int | float | Decimal | str,
        currency: str = "aed",
        metadata: Mapping[str, Any] | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        normalized_amount = self._normalize_amount(amount)
        safe_currency = (currency or self.default_currency).lower()
        safe_metadata = dict(metadata or {})

        if not self.stripe_api_key or self.stripe_api_key == "sk_test_placeholder":
            return {
                "success": True,
                "status": "mock",
                "client_secret": "mock_client_secret",
                "payment_intent_id": "mock_payment_intent_id",
                "amount": normalized_amount,
                "currency": safe_currency,
                "metadata": safe_metadata,
                "description": description,
            }

        stripe.api_key = self.stripe_api_key

        try:
            intent = stripe.PaymentIntent.create(
                amount=normalized_amount,
                currency=safe_currency,
                description=description,
                metadata=safe_metadata,
            )
            return {
                "success": True,
                "status": intent.status,
                "client_secret": intent.client_secret or "",
                "payment_intent_id": intent.id,
                "amount": normalized_amount,
                "currency": safe_currency,
                "metadata": safe_metadata,
                "description": description,
            }
        except Exception as exc:  # pragma: no cover - external API call
            logger.exception("Stripe payment intent creation failed")
            return {
                "success": False,
                "status": "failed",
                "client_secret": "",
                "payment_intent_id": None,
                "amount": normalized_amount,
                "currency": safe_currency,
                "metadata": safe_metadata,
                "description": description,
                "message": str(exc),
            }

    def verify_payment(self, payment_intent_id: str) -> dict[str, Any]:
        if not payment_intent_id:
            raise ValueError("Payment intent id is required.")

        if not self.stripe_api_key or self.stripe_api_key == "sk_test_placeholder":
            return {
                "success": True,
                "status": "succeeded",
                "payment_intent_id": payment_intent_id,
                "message": "Mock payment verification succeeded.",
            }

        stripe.api_key = self.stripe_api_key

        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "success": True,
                "status": intent.status,
                "payment_intent_id": intent.id,
                "amount": intent.amount,
                "currency": intent.currency,
            }
        except Exception as exc:  # pragma: no cover - external API call
            logger.exception("Stripe payment verification failed")
            return {
                "success": False,
                "status": "failed",
                "payment_intent_id": payment_intent_id,
                "message": str(exc),
            }


payment_service = PaymentService()
