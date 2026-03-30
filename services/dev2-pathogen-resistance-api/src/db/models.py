"""SQLAlchemy ORM models for database tables."""

from sqlalchemy import Column, String, Float, DateTime, UUID, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON
import uuid
from datetime import datetime

Base = declarative_base()


class ResistanceResult(Base):
    """
    Storage for antibiotic resistance prediction results.
    
    Supports soft deletes via deleted_at timestamp.
    One row per antibiotic prediction per analysis.
    """
    __tablename__ = "resistance_results"
    
    result_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    patient_id = Column(String(255), nullable=False, index=True)
    sample_id = Column(String(255), nullable=True, index=True)
    antibiotic = Column(String(255), nullable=False, index=True)
    prediction = Column(String(50), nullable=False)  # "Resistant", "Susceptible", "Intermediate"
    confidence_score = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False, default="v1")
    recommended_alternatives = Column(JSON, nullable=True)  # JSON array of alternatives
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete timestamp
    
    def __repr__(self):
        return (
            f"<ResistanceResult(result_id={self.result_id}, "
            f"patient_id={self.patient_id}, antibiotic={self.antibiotic}, "
            f"prediction={self.prediction})>"
        )


class AuditLog(Base):
    """
    Audit trail for tracking database modifications.
    
    Logs all INSERT and DELETE operations.
    """
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(50), nullable=False, index=True)  # INSERT, UPDATE, DELETE
    table_name = Column(String(255), nullable=False, index=True)
    record_id = Column(UUID(as_uuid=True), nullable=False)
    details = Column(JSON, nullable=True)  # Additional context
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return (
            f"<AuditLog(action={self.action}, "
            f"table_name={self.table_name}, record_id={self.record_id})>"
        )
