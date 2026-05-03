"""Database repository for resistance results operations."""

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from src.db.models import ResistanceResult, AuditLog


def store_resistance_result(
    db: Session,
    patient_id: str,
    sample_id: Optional[str],
    antibiotic: str,
    prediction: str,
    confidence_score: float,
    model_version: str = "v1",
    recommended_alternatives: Optional[List[str]] = None,
) -> ResistanceResult:
    """
    Store a single resistance prediction result.
    
    Args:
        db: Database session
        patient_id: Patient identifier
        sample_id: Optional sample identifier
        antibiotic: Antibiotic name
        prediction: Prediction result ("Resistant", "Susceptible", "Intermediate")
        confidence_score: Confidence score (0-1)
        model_version: Model version used for prediction
        recommended_alternatives: List of alternative antibiotics if resistant
        
    Returns:
        Created ResistanceResult record
    """
    result = ResistanceResult(
        patient_id=patient_id,
        sample_id=sample_id,
        antibiotic=antibiotic,
        prediction=prediction,
        confidence_score=confidence_score,
        model_version=model_version,
        recommended_alternatives=recommended_alternatives,
    )
    
    db.add(result)
    db.flush()  # Get the result_id
    
    # Log the insertion
    log_audit(db, "INSERT", "resistance_results", result.result_id, {
        "patient_id": patient_id,
        "antibiotic": antibiotic,
        "prediction": prediction,
    })
    
    db.commit()
    return result


def store_prediction_batch(
    db: Session,
    patient_id: str,
    sample_id: Optional[str],
    predictions: List[Dict[str, Any]],
    model_version: str = "v1",
    recommended_alternatives: Optional[List[str]] = None,
) -> List[ResistanceResult]:
    """
    Store multiple resistance predictions at once.
    
    Args:
        db: Database session
        patient_id: Patient identifier
        sample_id: Optional sample identifier
        predictions: List of prediction dicts with keys:
                     {antibiotic, result, confidence, shap_values}
        model_version: Model version used
        recommended_alternatives: Common alternatives for resistant predictions
        
    Returns:
        List of created ResistanceResult records
    """
    results = []
    
    for pred in predictions:
        result = ResistanceResult(
            patient_id=patient_id,
            sample_id=sample_id,
            antibiotic=pred["antibiotic"],
            prediction=pred["result"],
            confidence_score=pred["confidence"],
            model_version=model_version,
            recommended_alternatives=recommended_alternatives,
        )
        results.append(result)
        db.add(result)
        db.flush()
        
        # Log the insertion
        log_audit(db, "INSERT", "resistance_results", result.result_id, {
            "patient_id": patient_id,
            "antibiotic": pred["antibiotic"],
            "prediction": pred["result"],
        })
    
    db.commit()
    return results


def get_resistance_results(
    db: Session,
    patient_id: str,
    antibiotic: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[List[ResistanceResult], int]:
    """
    Retrieve resistance results for a patient with optional filtering.
    
    Args:
        db: Database session
        patient_id: Patient identifier
        antibiotic: Optional antibiotic filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Number of results to return
        offset: Pagination offset
        
    Returns:
        Tuple of (results list, total count)
    """
    query = db.query(ResistanceResult).filter(
        and_(
            ResistanceResult.patient_id == patient_id,
            ResistanceResult.deleted_at.is_(None),
        )
    )
    
    # Apply optional filters
    if antibiotic:
        query = query.filter(ResistanceResult.antibiotic == antibiotic)
    
    if start_date:
        query = query.filter(ResistanceResult.created_at >= start_date)
    
    if end_date:
        query = query.filter(ResistanceResult.created_at <= end_date)
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply sorting and pagination
    results = query.order_by(desc(ResistanceResult.created_at)).limit(limit).offset(offset).all()
    
    return results, total_count


def get_resistance_trend(
    db: Session,
    patient_id: str,
) -> Dict[str, Any]:
    """
    Get resistance trend data grouped by antibiotic.
    
    Args:
        db: Database session
        patient_id: Patient identifier
        
    Returns:
        Dictionary with trend data organized by antibiotic
    """
    results = db.query(ResistanceResult).filter(
        and_(
            ResistanceResult.patient_id == patient_id,
            ResistanceResult.deleted_at.is_(None),
        )
    ).order_by(asc(ResistanceResult.created_at)).all()
    
    # Group by antibiotic
    trend_data = {}
    for result in results:
        if result.antibiotic not in trend_data:
            trend_data[result.antibiotic] = []
        
        trend_data[result.antibiotic].append({
            "prediction": result.prediction,
            "confidence": result.confidence_score,
            "created_at": result.created_at.isoformat(),
        })
    
    return {
        "patient_id": patient_id,
        "trend": [
            {
                "antibiotic": antibiotic,
                "history": history,
            }
            for antibiotic, history in sorted(trend_data.items())
        ],
    }


def soft_delete_result(db: Session, result_id: uuid.UUID) -> Optional[ResistanceResult]:
    """
    Soft delete a resistance result by setting deleted_at timestamp.
    
    Args:
        db: Database session
        result_id: Result ID to delete
        
    Returns:
        Updated ResistanceResult or None if not found
    """
    result = db.query(ResistanceResult).filter(
        ResistanceResult.result_id == result_id
    ).first()
    
    if result:
        result.deleted_at = datetime.utcnow()
        db.commit()
        
        # Log the deletion
        log_audit(db, "DELETE", "resistance_results", result_id, {
            "patient_id": result.patient_id,
            "antibiotic": result.antibiotic,
        })
    
    return result


def log_audit(
    db: Session,
    action: str,
    table_name: str,
    record_id: uuid.UUID,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Log an audit trail entry.
    
    Args:
        db: Database session
        action: Action type (INSERT, UPDATE, DELETE)
        table_name: Name of table modified
        record_id: ID of modified record
        details: Optional additional context
        
    Returns:
        Created AuditLog record
    """
    log = AuditLog(
        action=action,
        table_name=table_name,
        record_id=record_id,
        details=details,
    )
    db.add(log)
    db.commit()
    return log
