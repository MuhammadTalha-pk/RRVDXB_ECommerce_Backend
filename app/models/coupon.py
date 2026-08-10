from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL
from sqlalchemy.sql import func
from app.core.database import Base

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    discount_type = Column(String(20))
    discount_value = Column(DECIMAL(10, 2))
    min_order = Column(DECIMAL(10, 2))
    max_discount = Column(DECIMAL(10, 2))
    expiry_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    used_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
