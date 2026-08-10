from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'))
    comment = Column(String)
    sentiment = Column(String(20))
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
