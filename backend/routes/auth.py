from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from backend.database.connection import get_db
from backend.database.models import User
from backend.auth.security import get_password_hash, verify_password
from backend.auth.jwt import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=72)
    confirm_password: str

class UserLogin(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # 1. Validation
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )
        
    # 2. Hash password & create user
    hashed_pwd = get_password_hash(user_data.password)
    
    # Create the first registered user as admin for demonstration purposes
    # Alternatively, check database to see if this is the first user
    is_first_user = db.query(User).count() == 0
    
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hashed_pwd,
        is_admin=is_first_user # First user is admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully", "user_id": new_user.id}

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Generate token
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }
