from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter
from datetime import datetime, timedelta, timezone
from backend.database.connection import get_db
from backend.database.models import User, Prediction
from backend.auth.jwt import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])

def parse_symptoms(raw_symptoms: str) -> list[str]:
    try:
        import json
        parsed = json.loads(raw_symptoms)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except Exception:
        pass
    return [s.strip() for s in raw_symptoms.split(",") if s.strip()] if raw_symptoms else []

@router.get("/stats")
def get_admin_stats(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    # 1. Total counts
    total_users = db.query(User).count()
    total_checks = db.query(Prediction).count()
    
    # 2. Most predicted diseases & distribution
    disease_counts = db.query(
        Prediction.prediction, 
        func.count(Prediction.id).label("count")
    ).group_by(Prediction.prediction).order_by(func.count(Prediction.id).desc()).all()
    
    disease_labels = [d[0] for d in disease_counts]
    disease_data = [d[1] for d in disease_counts]
    
    # 3. Most common symptoms
    # Query all predictions symptoms
    all_symptoms_queries = db.query(Prediction.symptoms).all()
    symptoms_counter = Counter()
    for query in all_symptoms_queries:
        if query[0]:
            symptoms = [s.strip().replace('_', ' ').title() for s in parse_symptoms(query[0])]
            symptoms_counter.update(symptoms)
            
    # Get top 10 symptoms
    top_symptoms = symptoms_counter.most_common(10)
    symptom_labels = [s[0] for s in top_symptoms]
    symptom_data = [s[1] for s in top_symptoms]
    
    # 4. User registrations over time (last 7 days)
    today = datetime.now(timezone.utc).date()
    registration_dates = {}
    for i in range(7):
        date = today - timedelta(days=i)
        registration_dates[date.strftime("%Y-%m-%d")] = 0
        
    # Query registrations in last 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_users = db.query(User).filter(User.created_at >= seven_days_ago).all()
    
    for u in recent_users:
        date_str = u.created_at.strftime("%Y-%m-%d")
        if date_str in registration_dates:
            registration_dates[date_str] += 1
            
    # Sort dates chronologically
    sorted_dates = sorted(registration_dates.keys())
    reg_data = [registration_dates[d] for d in sorted_dates]
    
    return {
        "summary": {
            "total_users": total_users,
            "total_health_checks": total_checks
        },
        "diseases": {
            "labels": disease_labels[:10], # Top 10 diseases
            "data": disease_data[:10]
        },
        "symptoms": {
            "labels": symptom_labels,
            "data": symptom_data
        },
        "registrations": {
            "labels": sorted_dates,
            "data": reg_data
        }
    }
