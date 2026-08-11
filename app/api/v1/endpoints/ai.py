from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db  # project ka database session path
from app.schemas import coupon_schema as schemas
from app.ai.deal_finder import find_best_ai_deals, get_flash_deal_alerts
from app.services import ai_service

from app.ai.trend_analyzer import analyze_shopping_trends

router = APIRouter()

@router.get("/trends")
def get_shopping_trends():
    """
    AI Trend Analyzer endpoint.
    Assigned to: Muhammad Talha
    """
    return analyze_shopping_trends()



@router.get("/deals", response_model=schemas.AIDealsResponse)
def get_ai_deals(db: Session = Depends(get_db)):
    return find_best_ai_deals(db)

@router.post("/coupons/generate", response_model=schemas.CouponResponse, status_code=status.HTTP_201_CREATED)
def generate_coupon(coupon_data: schemas.CouponCreate, db: Session = Depends(get_db)):
    return coupon_service.create_coupon(db, coupon_data)

@router.post("/coupons/validate")
def validate_coupon(payload: schemas.CouponValidate, db: Session = Depends(get_db)):
    coupon = coupon_service.validate_and_apply_coupon(db, payload.code, payload.order_amount)
    return {
        "valid": True,
        "code": coupon.code,
        "discountType": coupon.discount_type,
        "discountValue": float(coupon.discount_value),
        "message": "Coupon is valid and ready to apply."
    }

@router.get("/flash-deals/alerts")
def get_flash_deal_alerts_endpoint(threshold_hours: int = 3, db: Session = Depends(get_db)):
    alerts = get_flash_deal_alerts(db, threshold_hours=threshold_hours)
    return {
        "count": len(alerts),
        "alerts": alerts
    }
