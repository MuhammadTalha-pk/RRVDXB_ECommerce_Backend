from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.product_schema import ProductResponse

class CartItemBase(BaseModel):
    product_id: int
    quantity: int = 1
    size: Optional[str] = None
    color: Optional[str] = None

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(CartItemBase):
    id: int
    user_id: int
    added_at: datetime
    # We might want to return the product details as well
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True
