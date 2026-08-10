from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class WalletBase(BaseModel):
    balance: Decimal

class WalletResponse(WalletBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WalletAddMoney(BaseModel):
    amount: Decimal
    payment_method_id: Optional[str] = None # For Stripe

class WalletTransactionResponse(BaseModel):
    id: int
    wallet_id: int
    amount: Decimal
    type: str
    description: Optional[str] = None
    reference_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
