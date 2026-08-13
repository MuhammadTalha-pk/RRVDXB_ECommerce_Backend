from decimal import Decimal

import pytest

from app.services.payment_service import PaymentService, payment_service


def test_payment_service_returns_mock_client_secret_without_stripe_key():
    service = PaymentService()

    result = service.create_payment_intent(amount=1000, currency="aed")

    assert result["success"] is True
    assert result["client_secret"] == "mock_client_secret"
    assert result["amount"] == 1000
    assert result["currency"] == "aed"


def test_payment_service_validates_amount():
    service = PaymentService()

    with pytest.raises(ValueError):
        service.create_payment_intent(amount=0)


def test_global_service_instance_exists():
    assert isinstance(payment_service, PaymentService)
    assert callable(payment_service.create_payment_intent)
