from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app import models

def get_time_remaining_str(end_time: datetime) -> str:
    """Helper function to format remaining time like '2 hours' or '45 mins'."""
    now = datetime.now()
    if end_time.tzinfo is not None:
        now = datetime.now(timezone.utc)

    diff = end_time - now
    if diff.total_seconds() <= 0:
        return "Expired"

    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)

    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''}"
    elif minutes > 0:
        return f"{minutes} min{'s' if minutes > 1 else ''}"
    else:
        return "Less than a minute"


def find_best_ai_deals(db: Session):
    """
    1. Scans FlashSale table for active flash sales.
    2. Scans Products table for best discounts (price vs old_price).
    3. Fetches active, valid Coupon codes.
    4. Constructs the expected AI JSON structure.
    """
    best_deals = []

    # --- A. Check Active Flash Sales ---
    now = datetime.now()
    active_flash_sales = db.query(models.FlashSale).filter(
        and_(
            models.FlashSale.is_active == True,
            models.FlashSale.end_time > now
        )
    ).all()

    flash_product_ids = set()

    for flash in active_flash_sales:
        product = db.query(models.Product).filter(models.Product.id == flash.product_id).first()
        if product and product.is_available:
            flash_product_ids.add(product.id)
            orig_price = float(product.old_price if product.old_price else product.price)
            curr_price = float(flash.flash_price)
            discount_val = orig_price - curr_price

            best_deals.append({
                "productId": f"P{product.id:03d}",
                "originalPrice": orig_price,
                "currentPrice": curr_price,
                "discount": round(discount_val, 2),
                "dealType": "Flash Sale",
                "expiresIn": get_time_remaining_str(flash.end_time)
            })

    # --- B. Check Regular Discounted Products ---
    discounted_products = db.query(models.Product).filter(
        and_(
            models.Product.is_available == True,
            models.Product.old_price.isnot(None),
            models.Product.old_price > models.Product.price
        )
    ).order_by((models.Product.old_price - models.Product.price).desc()).limit(10).all()

    for prod in discounted_products:
        if prod.id not in flash_product_ids:
            orig_price = float(prod.old_price)
            curr_price = float(prod.price)
            discount_val = orig_price - curr_price

            best_deals.append({
                "productId": f"P{prod.id:03d}",
                "originalPrice": orig_price,
                "currentPrice": curr_price,
                "discount": round(discount_val, 2),
                "dealType": "Discount",
                "expiresIn": "Limited Time"
            })

    best_deals = sorted(best_deals, key=lambda x: x["discount"], reverse=True)

    # --- C. Get Active Coupon Codes ---
    active_coupons = db.query(models.Coupon.code).filter(
        and_(
            models.Coupon.is_active == True,
            models.Coupon.expiry_date > now
        )
    ).all()

    coupon_list = [c.code for c in active_coupons]

    return {
        "bestDeals": best_deals,
        "coupons": coupon_list
    }


def get_flash_deal_alerts(db: Session, threshold_hours: int = 3):
    """
    Flash Deal Alert: Finds flash deals ending within threshold_hours.
    """
    now = datetime.now()
    urgent_alerts = []

    active_flash_sales = db.query(models.FlashSale).filter(
        and_(
            models.FlashSale.is_active == True,
            models.FlashSale.end_time > now
        )
    ).all()

    for flash in active_flash_sales:
        diff_hours = (flash.end_time - now).total_seconds() / 3600
        if diff_hours <= threshold_hours:
            product = db.query(models.Product).filter(models.Product.id == flash.product_id).first()
            if product:
                urgent_alerts.append({
                    "alertType": "FLASH_SALE_ENDING_SOON",
                    "productId": f"P{product.id:03d}",
                    "productName": product.name,
                    "flashPrice": float(flash.flash_price),
                    "originalPrice": float(product.old_price or product.price),
                    "expiresIn": get_time_remaining_str(flash.end_time)
                })

    return urgent_alerts