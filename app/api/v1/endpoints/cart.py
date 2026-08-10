from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db, get_current_user
from app.models.cart import Cart
from app.models.user import User
from app.schemas.cart_schema import CartItemCreate, CartItemUpdate, CartItemResponse

router = APIRouter()

@router.get("/", response_model=List[CartItemResponse])
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
    return cart_items

@router.post("/add", response_model=CartItemResponse)
def add_to_cart(
    item_in: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if item already exists in cart
    existing_item = db.query(Cart).filter(
        Cart.user_id == current_user.id,
        Cart.product_id == item_in.product_id,
        Cart.size == item_in.size,
        Cart.color == item_in.color
    ).first()

    if existing_item:
        existing_item.quantity += item_in.quantity
        db.commit()
        db.refresh(existing_item)
        return existing_item

    new_item = Cart(**item_in.model_dump(), user_id=current_user.id)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.put("/update/{id}", response_model=CartItemResponse)
def update_cart_item(
    id: int,
    item_in: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(Cart).filter(Cart.id == id, Cart.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    item.quantity = item_in.quantity
    db.commit()
    db.refresh(item)
    return item

@router.delete("/remove/{id}")
def remove_from_cart(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(Cart).filter(Cart.id == id, Cart.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.delete(item)
    db.commit()
    return {"msg": "Item removed from cart"}

@router.delete("/clear")
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Cart).filter(Cart.user_id == current_user.id).delete()
    db.commit()
    return {"msg": "Cart cleared"}
