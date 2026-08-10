from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.order import Order
from app.models.product import Product
from app.models.wallet import WalletTransaction

router = APIRouter()

@router.get("/dashboard")
def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    total_users = db.query(func.count(User.id)).scalar()
    total_orders = db.query(func.count(Order.id)).scalar()
    total_products = db.query(func.count(Product.id)).scalar()
    
    # Calculate total sales (sum of total_amount from all delivered orders)
    total_sales_query = db.query(func.sum(Order.total_amount)).filter(Order.order_status == "delivered").scalar()
    total_sales = float(total_sales_query) if total_sales_query else 0.0

    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "total_products": total_products,
        "total_sales": total_sales
    }
