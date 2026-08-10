from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
from decimal import Decimal

class OrderItemSchema(BaseModel):
    product_id: int
    quantity: int
    price: Decimal

class OrderBase(BaseModel):
    shipping_address: str
    payment_method: Optional[str] = None
    coupon: Optional[str] = None

class OrderCreate(OrderBase):
    items: List[OrderItemSchema] # Used for request validation

class OrderStatusUpdate(BaseModel):
    order_status: str

class OrderResponse(OrderBase):
    id: int
    user_id: int
    order_number: str
    items: Any # JSONB in DB
    payment_status: str
    order_status: str
    subtotal: Decimal
    tax: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
    discount: Optional[Decimal] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
