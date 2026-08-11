
import random
import string
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import models
import schemas
from decimal import Decimal

def generate_random_code(prefix: str = "DEAL", length: int = 6) -> str:
    """Generates a code like DEAL8X2K9P"""
    chars = string.ascii_uppercase + string.digits
    random_str = ''.join(random.choices(chars, k=length))
    return f"{prefix}{random_str}"

def create_coupon(db: Session, coupon_data: schemas.CouponCreate) -> models.Coupon:
    # Auto-generate a code if the user didn't supply one
    code = coupon_data.code.upper() if coupon_data.code else generate_random_code()
    
    # Check if code already exists
    existing = db.query(models.Coupon).filter(models.Coupon.code == code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Coupon code '{code}' already exists."
        )

    db_coupon = models.Coupon(
        code=code,
        discount_type=coupon_data.discount_type,
        discount_value=coupon_data.discount_value,
        min_order=coupon_data.min_order,
        max_discount=coupon_data.max_discount,
        expiry_date=coupon_data.expiry_date,
        is_active=coupon_data.is_active,
        used_count=0
    )
    db.add(db_coupon)
    db.commit()
    db.refresh(db_coupon)
    return db_coupon

def validate_and_apply_coupon(db: Session, code: str, order_amount: float):
    coupon = db.query(models.Coupon).filter(models.Coupon.code == code).first()
    
    if not coupon or not coupon.is_active:
        raise HTTPException(status_code=400, detail="Invalid or inactive coupon.")
    
    if coupon.expiry_date and coupon.expiry_date < datetime.now():
        raise HTTPException(status_code=400, detail="Coupon has expired.")
        
    if coupon.min_order and Decimal(str(order_amount)) < coupon.min_order:
        raise HTTPException(status_code=400, detail=f"Minimum order amount for this coupon is {coupon.min_order}")

    return coupon

from typing import Any

from app.ai.sentiment_analyzer import (
    sentiment_analyzer,
)


class AIService:
    def analyze_sentiment(
        self,
        review: str,
    ) -> dict[str, Any]:
        return sentiment_analyzer.analyze(review)

    def get_status(self) -> dict[str, Any]:
        return {
            "success": True,
            "service": "RRVDXB AI Service",
            "status": "operational",
            "modules": {
                "sentimentAnalyzer": "available",
            },
        }


ai_service = AIService()
