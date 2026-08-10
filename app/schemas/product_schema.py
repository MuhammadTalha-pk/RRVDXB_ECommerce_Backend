from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class CategoryCreate(CategoryBase):
    slug: str

class CategoryResponse(CategoryBase):
    id: int
    slug: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Brand Schemas
class BrandBase(BaseModel):
    name: str
    logo: Optional[str] = None

class BrandCreate(BrandBase):
    pass

class BrandResponse(BrandBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    old_price: Optional[Decimal] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    images: Optional[List[str]] = []
    stock: int = 0
    is_featured: bool = False
    is_best_seller: bool = False

class ProductCreate(ProductBase):
    slug: str

class ProductUpdate(ProductBase):
    name: Optional[str] = None
    price: Optional[Decimal] = None

class ProductResponse(ProductBase):
    id: int
    slug: str
    is_available: bool
    average_rating: Decimal
    created_at: datetime

    class Config:
        from_attributes = True
