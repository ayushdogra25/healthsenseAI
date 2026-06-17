from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from backend.database.connection import get_db
from backend.database.models import User, Prediction
from backend.auth.jwt import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])

class ProfileUpdate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=50)
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = Field(None, max_length=20)

@router.get("")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Calculate statistics
    total_checks = db.query(Prediction).filter(Prediction.user_id == current_user.id).count()
    last_check = db.query(Prediction).filter(Prediction.user_id == current_user.id).order_by(Prediction.created_at.desc()).first()
    
    last_check_date = last_check.created_at if last_check else None
    
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "age": current_user.age,
        "gender": current_user.gender,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at,
        "stats": {
            "total_health_checks": total_checks,
            "last_check_date": last_check_date
        }
    }

@router.put("")
def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.full_name = profile_data.full_name
    current_user.age = profile_data.age
    current_user.gender = profile_data.gender
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Profile updated successfully",
        "user": {
            "full_name": current_user.full_name,
            "email": current_user.email,
            "age": current_user.age,
            "gender": current_user.gender
        }
    }
