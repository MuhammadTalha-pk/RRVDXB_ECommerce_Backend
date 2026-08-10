from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from decimal import Decimal
from app.core.dependencies import get_db, get_current_user
from app.models.order import Order
from app.models.user import User
from app.schemas.order_schema import OrderCreate, OrderResponse, OrderStatusUpdate

router = APIRouter()

@router.post("/", response_model=OrderResponse)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Generate unique order number
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    # Calculate totals (Simplified)
    subtotal = sum(item.price * item.quantity for item in order_in.items)
    tax = subtotal * Decimal('0.05') # 5% tax
    delivery_fee = Decimal('20.00') if subtotal < Decimal('489.00') else Decimal('0.00')
    discount = Decimal('0.00') # Would calculate based on coupon
    total_amount = subtotal + tax + delivery_fee - discount

    # Convert items to dict for JSONB
    items_list = [item.model_dump() for item in order_in.items]
    items_list_str_price = [{**i, "price": str(i["price"])} for i in items_list] # JSON serialization

    order = Order(
        user_id=current_user.id,
        order_number=order_number,
        items=items_list_str_price,
        shipping_address=order_in.shipping_address,
        payment_method=order_in.payment_method,
        subtotal=subtotal,
        tax=tax,
        delivery_fee=delivery_fee,
        total_amount=total_amount,
        coupon=order_in.coupon,
        discount=discount
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/", response_model=List[OrderResponse])
def get_user_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.query(Order).filter(Order.user_id == current_user.id).all()
    return orders

@router.get("/{id}", response_model=OrderResponse)
def get_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.get("/{id}/track")
def track_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_number": order.order_number, "status": order.order_status}

@router.put("/{id}/status", response_model=OrderResponse)
def update_order_status(
    id: int,
    status_in: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.order_status = status_in.order_status
    db.commit()
    db.refresh(order)
    return order
