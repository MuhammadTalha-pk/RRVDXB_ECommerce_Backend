from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db, get_current_user
from app.models.category import Category
from app.models.user import User
from app.schemas.product_schema import CategoryCreate, CategoryResponse

router = APIRouter()

@router.get("/", response_model=List[CategoryResponse])
def read_categories(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories

@router.post("/", response_model=CategoryResponse)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    category = Category(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
