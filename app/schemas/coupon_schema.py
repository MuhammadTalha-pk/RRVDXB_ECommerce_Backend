from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- Coupon Schemas ---
class CouponCreate(BaseModel):
    code: Optional[str] = None  # If empty, we can auto-generate one!
    discount_type: str = Field(..., description="'percentage' or 'fixed'")
    discount_value: Decimal
    min_order: Optional[Decimal] = Decimal("0.00")
    max_discount: Optional[Decimal] = None
    expiry_date: datetime
    is_active: bool = True

class CouponResponse(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: Decimal
    min_order: Optional[Decimal]
    max_discount: Optional[Decimal]
    expiry_date: datetime
    is_active: bool
    used_count: int

    class Config:
        from_attributes = True

class CouponValidate(BaseModel):
    code: str
    order_amount: Decimal

# --- AI Deal Finder Response Schemas ---
class DealItem(BaseModel):
    productId: str
    originalPrice: float
    currentPrice: float
    discount: float
    dealType: str
    expiresIn: str

class AIDealsResponse(BaseModel):
    bestDeals: List[DealItem]
    coupons: List[str]