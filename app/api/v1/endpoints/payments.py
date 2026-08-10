from fastapi import APIRouter, Depends, HTTPException
import stripe
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

stripe.api_key = settings.STRIPE_API_KEY

@router.post("/create-payment-intent")
def create_payment_intent(
    amount: int, # amount in cents
    current_user: User = Depends(get_current_user)
):
    if not settings.STRIPE_API_KEY or settings.STRIPE_API_KEY == "sk_test_placeholder":
        # Return mock data if Stripe is not configured
        return {"clientSecret": "mock_client_secret"}
        
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="aed",
            metadata={"user_id": current_user.id}
        )
        return {"clientSecret": "mock_client_secret" if not intent.client_secret else intent.client_secret} # Using mock fallback for safety if something weird happens
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
