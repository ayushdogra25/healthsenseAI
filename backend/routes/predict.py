import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database.connection import get_db
from backend.database.models import Prediction
from backend.auth.jwt import get_current_user
from backend.database.models import User
from backend.ml.predict import predictor
from backend.services.gemini import generate_explanation

router = APIRouter(prefix="/api", tags=["prediction"])

class PredictRequest(BaseModel):
    symptoms: list[str]

def calculate_risk_score(symptoms: list[str], primary_disease: str) -> int:
    """
    Computes a mock but realistic risk score (0-100) based on symptom count,
    presence of severe symptoms, and disease severity markers.
    """
    score = 10
    
    # Severe symptoms list
    severe_symptoms = [
        "shortness of breath", "chest pain", "difficulty breathing", 
        "stiff neck", "confusion", "loss of consciousness", 
        "irregular heartbeat", "vision loss", "numbness", 
        "muscle weakness", "paralysis", "blood in stool", "coughing blood",
        "severe pain", "neck pain", "back pain", "abdominal pain"
    ]
    
    # Check for severe symptoms
    has_severe = False
    for s in symptoms:
        cleaned_s = s.lower().strip()
        # Direct check or substring match
        if any(severe in cleaned_s or cleaned_s in severe for severe in severe_symptoms):
            score += 35
            has_severe = True
            break # Apply severe symptom bump once
            
    # Symptom count adjustment (more symptoms = higher complexity)
    score += len(symptoms) * 4
    
    # Disease severity weight
    severe_diseases = [
        "covid 19", "influenza", "hypertension", "pneumonia", 
        "bronchitis", "heart disease", "diabetes", "hepatitis", 
        "tuberculosis", "kidney disease", "typhoid", "malaria"
    ]
    
    disease_clean = primary_disease.lower()
    if any(sd in disease_clean for sd in severe_diseases):
        score += 20
    else:
        score += 5
        
    # Cap score between 0 and 100
    return min(100, max(0, score))

@router.post("/predict")
def predict_health(request: PredictRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not request.symptoms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one symptom must be provided."
        )
        
    try:
        # 1. Run Machine Learning Model Prediction
        prediction_results = predictor.predict_diseases(request.symptoms)
        predictions = prediction_results["predictions"]  # list of top 3 predictions
        matched_symptoms = prediction_results["matched_symptoms"]
        
        if not predictions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ML model did not return any predictions."
            )
            
        primary_disease = predictions[0]["disease"]
        primary_confidence = predictions[0]["confidence"]
        
        # 2. Calculate Health Risk Score
        risk_score = calculate_risk_score(request.symptoms, primary_disease)
        
        # 3. Call Gemini AI explanation service
        # Using a list of symptoms, or matched symptoms if preferred
        ai_explanation = generate_explanation(primary_disease, primary_confidence, request.symptoms)
        
        # 4. Save to Database
        new_prediction = Prediction(
            user_id=current_user.id,
            symptoms=json.dumps(request.symptoms),
            prediction=primary_disease,
            confidence=primary_confidence,
            all_predictions=json.dumps(predictions),
            risk_score=risk_score,
            ai_explanation=ai_explanation
        )
        
        db.add(new_prediction)
        db.commit()
        db.refresh(new_prediction)
        
        return {
            "prediction_id": new_prediction.id,
            "symptoms_entered": request.symptoms,
            "matched_symptoms": matched_symptoms,
            "top_diseases": predictions,
            "risk_score": risk_score,
            "ai_explanation": ai_explanation,
            "created_at": new_prediction.created_at
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during prediction: {str(e)}"
        )

@router.get("/symptoms-list")
def get_all_symptoms():
    """
    Returns the full list of 377 symptoms that the model is trained on.
    Used for the searchable dropdown on the frontend.
    """
    if predictor.symptom_columns is None:
        # Attempt reloading
        predictor.load_assets()
        
    if predictor.symptom_columns is None:
        # Fallback list if assets aren't built yet
        return ["fever", "cough", "headache", "shortness of breath", "fatigue", "nausea", "vomiting", "sore throat", "diarrhea"]
        
    return predictor.symptom_columns
