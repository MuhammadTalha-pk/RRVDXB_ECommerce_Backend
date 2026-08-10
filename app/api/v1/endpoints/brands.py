from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db, get_current_user
from app.models.brand import Brand
from app.models.user import User
from app.schemas.product_schema import BrandCreate, BrandResponse

router = APIRouter()

@router.get("/", response_model=List[BrandResponse])
def read_brands(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    brands = db.query(Brand).offset(skip).limit(limit).all()
    return brands

@router.post("/", response_model=BrandResponse)
def create_brand(
    brand_in: BrandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    brand = Brand(**brand_in.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand
