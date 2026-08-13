from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.payment_service import payment_service

router = APIRouter()


@router.post("/create-payment-intent")
def create_payment_intent(
    amount: int,
    current_user: User = Depends(get_current_user),
):
    try:
        result = payment_service.create_payment_intent(
            amount=amount,
            currency="aed",
            metadata={"user_id": current_user.id},
            description="RRVDXB checkout payment",
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Payment failed"))
        return {
            "clientSecret": result.get("client_secret"),
            "paymentIntentId": result.get("payment_intent_id"),
            "status": result.get("status"),
            "amount": result.get("amount"),
            "currency": result.get("currency"),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
