from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database.connection import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symptoms = Column(Text, nullable=False)  # JSON string of user-entered symptoms
    prediction = Column(String, nullable=False)  # Main predicted disease
    confidence = Column(Float, nullable=False)  # Main disease confidence percentage
    all_predictions = Column(Text, nullable=False)  # JSON string of top 3 predictions
    risk_score = Column(Integer, nullable=False)
    ai_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    user = relationship("User", back_populates="predictions")
    reports = relationship("Report", back_populates="prediction", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_predictions_risk_score_range"),
    )

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    pdf_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    user = relationship("User", back_populates="reports")
    prediction = relationship("Prediction", back_populates="reports")

    __table_args__ = (
        UniqueConstraint("prediction_id", name="uq_reports_prediction_id"),
    )
