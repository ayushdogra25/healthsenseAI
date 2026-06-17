import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from backend.database.connection import get_db
from backend.database.models import Prediction, User
from backend.auth.jwt import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])

def parse_symptoms(raw_symptoms: str) -> list[str]:
    try:
        parsed = json.loads(raw_symptoms)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except Exception:
        pass
    return raw_symptoms.split(", ") if raw_symptoms else []

@router.get("")
def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    sort: str = Query("desc"),  # "desc" or "asc"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Prediction).filter(Prediction.user_id == current_user.id)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Prediction.symptoms.ilike(search_term),
                Prediction.prediction.ilike(search_term)
            )
        )
        
    # Apply sorting
    if sort.lower() == "asc":
        query = query.order_by(asc(Prediction.created_at))
    else:
        query = query.order_by(desc(Prediction.created_at))
        
    # Pagination
    total = query.count()
    offset = (page - 1) * limit
    results = query.offset(offset).limit(limit).all()
    
    # Format predictions
    formatted_results = []
    for r in results:
        try:
            all_preds = json.loads(r.all_predictions)
        except Exception:
            all_preds = [{"disease": r.prediction, "confidence": r.confidence}]
            
        formatted_results.append({
            "id": r.id,
            "symptoms": parse_symptoms(r.symptoms),
            "prediction": r.prediction,
            "confidence": r.confidence,
            "all_predictions": all_preds,
            "risk_score": r.risk_score,
            "ai_explanation": r.ai_explanation,
            "created_at": r.created_at
        })
        
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "results": formatted_results
    }
