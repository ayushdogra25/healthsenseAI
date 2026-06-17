import os
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database.connection import get_db
from backend.database.models import Prediction, Report, User
from backend.auth.jwt import get_current_user
from backend.utils.pdf_generator import generate_pdf_report

router = APIRouter(prefix="/api/reports", tags=["reports"])

def parse_symptoms(raw_symptoms: str) -> list[str]:
    try:
        parsed = json.loads(raw_symptoms)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except Exception:
        pass
    return raw_symptoms.split(", ") if raw_symptoms else []

class ReportRequest(BaseModel):
    prediction_id: int

@router.post("/generate")
def create_report_record(request: ReportRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Fetch prediction
    prediction = db.query(Prediction).filter(Prediction.id == request.prediction_id).first()
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found."
        )
        
    # Verify ownership
    if prediction.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this prediction."
        )
        
    # 2. Check if report already generated
    existing_report = db.query(Report).filter(Report.prediction_id == prediction.id).first()
    if existing_report:
        return {
            "report_id": existing_report.id,
            "pdf_url": f"/static/reports/{os.path.basename(existing_report.pdf_path)}",
            "message": "Report already exists"
        }
        
    # 3. Generate PDF content and save to static folder
    try:
        # Create reports directory
        static_reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "reports")
        os.makedirs(static_reports_dir, exist_ok=True)
        
        filename = f"report_{prediction.id}_{current_user.id}.pdf"
        file_path = os.path.join(static_reports_dir, filename)
        
        # Load all predictions
        try:
            preds_list = json.loads(prediction.all_predictions)
        except Exception:
            preds_list = [{"disease": prediction.prediction, "confidence": prediction.confidence}]
            
        # Generate the PDF bytes
        pdf_buffer = generate_pdf_report(
            user_name=current_user.full_name,
            date_str=prediction.created_at.strftime("%B %d, %Y"),
            symptoms=parse_symptoms(prediction.symptoms),
            predictions=preds_list,
            risk_score=prediction.risk_score,
            ai_explanation=prediction.ai_explanation
        )
        
        # Write to disk
        with open(file_path, "wb") as f:
            f.write(pdf_buffer.getbuffer())
            
        # 4. Save to Database
        new_report = Report(
            user_id=current_user.id,
            prediction_id=prediction.id,
            pdf_path=file_path
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        return {
            "report_id": new_report.id,
            "pdf_url": f"/static/reports/{filename}",
            "message": "Report generated successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )

@router.get("/download/{prediction_id}")
def download_pdf(prediction_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found."
        )
        
    # Verify ownership
    if prediction.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this prediction."
        )
        
    # Generate the PDF stream
    try:
        try:
            preds_list = json.loads(prediction.all_predictions)
        except Exception:
            preds_list = [{"disease": prediction.prediction, "confidence": prediction.confidence}]
            
        pdf_buffer = generate_pdf_report(
            user_name=current_user.full_name,
            date_str=prediction.created_at.strftime("%B %d, %Y"),
            symptoms=parse_symptoms(prediction.symptoms),
            predictions=preds_list,
            risk_score=prediction.risk_score,
            ai_explanation=prediction.ai_explanation
        )
        
        headers = {
            'Content-Disposition': f'attachment; filename="healthsense_report_{prediction.id}.pdf"'
        }
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream report: {str(e)}"
        )
