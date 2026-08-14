from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    order_number = Column(String(50), unique=True, nullable=False)
    items = Column(JSON, nullable=False)
    shipping_address = Column(String, nullable=False)
    payment_method = Column(String(50))
    payment_status = Column(String(50), default="pending")
    order_status = Column(String(50), default="pending")
    subtotal = Column(DECIMAL(10, 2))
    tax = Column(DECIMAL(10, 2))
    delivery_fee = Column(DECIMAL(10, 2))
    total_amount = Column(DECIMAL(10, 2))
    coupon = Column(String(50))
    discount = Column(DECIMAL(10, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True))
