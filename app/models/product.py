from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, ARRAY
from sqlalchemy.sql import func
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True)
    description = Column(String)
    price = Column(DECIMAL(10, 2), nullable=False)
    old_price = Column(DECIMAL(10, 2))
    category_id = Column(Integer, ForeignKey("categories.id"))
    brand_id = Column(Integer, ForeignKey("brands.id"))
    images = Column(ARRAY(String))
    stock = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    is_best_seller = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    average_rating = Column(DECIMAL(3, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
