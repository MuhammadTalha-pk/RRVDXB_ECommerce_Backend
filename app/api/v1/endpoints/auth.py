from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.user_schema import UserCreate, UserResponse, Token

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=get_password_hash(user_in.password),
        phone=user_in.phone,
        address=user_in.address,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create a wallet for the user automatically
    wallet = Wallet(user_id=user.id)
    db.add(wallet)
    db.commit()

    return user

@router.post("/login", response_model=Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
def refresh_token(current_user: User = Depends(get_current_user)):
    # Simply issue a new token for the authenticated user
    access_token = create_access_token(data={"sub": current_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout():
    # Since we use stateless JWT, logout is usually handled client-side by deleting the token.
    # We could implement a token blocklist in DB/Redis for real logout.
    return {"msg": "Successfully logged out"}
