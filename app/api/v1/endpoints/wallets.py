from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db, get_current_user
from app.models.wallet import Wallet, WalletTransaction
from app.models.user import User
from app.schemas.wallet_schema import WalletResponse, WalletAddMoney, WalletTransactionResponse
import uuid

router = APIRouter()

@router.get("/", response_model=WalletResponse)
def get_wallet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet

@router.post("/add", response_model=WalletResponse)
def add_money(
    data: WalletAddMoney,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
        
    # In a real app, process payment with Stripe using data.payment_method_id here
    # Assuming payment is successful:
    
    wallet.balance += data.amount
    
    transaction = WalletTransaction(
        wallet_id=wallet.id,
        amount=data.amount,
        type="credit",
        description="Added money to wallet via card",
        reference_id=f"TXN-{uuid.uuid4().hex[:8].upper()}"
    )
    db.add(transaction)
    db.commit()
    db.refresh(wallet)
    return wallet

@router.get("/transactions", response_model=List[WalletTransactionResponse])
def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
        
    transactions = db.query(WalletTransaction).filter(WalletTransaction.wallet_id == wallet.id).order_by(WalletTransaction.created_at.desc()).all()
    return transactions
