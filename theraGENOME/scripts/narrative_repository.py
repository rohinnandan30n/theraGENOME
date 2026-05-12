"""
Narrative Report Repository (Task 4.5)

Database operations for storing and retrieving generated clinical narratives.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID
import json

from sqlalchemy import select, insert, update, delete, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Text, DateTime, Float, UUID as SQLUUID
import sqlalchemy

Base = declarative_base()


# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================

class NarrativeReport(Base):
    """ORM model for narrative clinical reports."""
    __tablename__ = "narrative_reports"
    
    id = Column(SQLUUID, primary_key=True, default=sqlalchemy.func.gen_random_uuid())
    therapy_report_id = Column(SQLUUID, nullable=False, index=True)
    patient_id = Column(SQLUUID, nullable=False, index=True)
    
    # Narrative content
    narrative_text = Column(Text, nullable=False)
    narrative_sections = Column(sqlalchemy.JSON, nullable=True)  # Parsed sections
    
    # SHAP explanations (stored as JSON)
    variant_shap_json = Column(sqlalchemy.JSON, nullable=True)
    resistance_shap_json = Column(sqlalchemy.JSON, nullable=True)
    toxicity_shap_json = Column(sqlalchemy.JSON, nullable=True)
    
    # Generation metadata
    llm_model_used = Column(String(255), nullable=False)  # e.g., "gpt-4-turbo" or "biomistral"
    generation_duration_seconds = Column(Float, nullable=True)
    generation_temperature = Column(Float, nullable=False, default=0.7)
    
    # Quality metrics
    readability_score = Column(Float, nullable=True)  # Flesch-Kincaid grade
    medical_terminology_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)  # 0-1, how complete the narrative is
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    created_by = Column(String(255), nullable=True)  # Clinician/service ID
    clinician_id = Column(String(255), nullable=True, index=True)
    
    __table_args__ = (
        sqlalchemy.Index("idx_narrative_reports_therapy_report_id", "therapy_report_id"),
        sqlalchemy.Index("idx_narrative_reports_patient_id", "patient_id"),
        sqlalchemy.Index("idx_narrative_reports_created_at_desc", desc("created_at")),
        sqlalchemy.Index("idx_narrative_reports_clinician_id", "clinician_id"),
        sqlalchemy.Index("idx_narrative_reports_deleted_at", "deleted_at"),
    )


class NarrativeReportRepository:
    """Database operations for narrative reports."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create(
        self,
        therapy_report_id: str,
        patient_id: str,
        narrative_text: str,
        llm_model_used: str,
        narrative_sections: Optional[dict] = None,
        variant_shap_json: Optional[dict] = None,
        resistance_shap_json: Optional[dict] = None,
        toxicity_shap_json: Optional[dict] = None,
        generation_duration_seconds: Optional[float] = None,
        generation_temperature: float = 0.7,
        clinician_id: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> dict:
        """Create a new narrative report."""
        
        report = NarrativeReport(
            therapy_report_id=therapy_report_id,
            patient_id=patient_id,
            narrative_text=narrative_text,
            narrative_sections=narrative_sections,
            variant_shap_json=variant_shap_json,
            resistance_shap_json=resistance_shap_json,
            toxicity_shap_json=toxicity_shap_json,
            llm_model_used=llm_model_used,
            generation_duration_seconds=generation_duration_seconds,
            generation_temperature=generation_temperature,
            clinician_id=clinician_id,
            created_by=created_by
        )
        
        self.db.add(report)
        await self.db.flush()
        
        return {
            "id": str(report.id),
            "therapy_report_id": str(report.therapy_report_id),
            "patient_id": str(report.patient_id),
            "created_at": report.created_at.isoformat()
        }
    
    async def get_by_id(self, narrative_id: str) -> Optional[dict]:
        """Get narrative report by ID."""
        stmt = select(NarrativeReport).where(
            and_(
                NarrativeReport.id == narrative_id,
                NarrativeReport.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(stmt)
        report = result.scalars().first()
        
        if not report:
            return None
        
        return {
            "id": str(report.id),
            "therapy_report_id": str(report.therapy_report_id),
            "patient_id": str(report.patient_id),
            "narrative_text": report.narrative_text,
            "narrative_sections": report.narrative_sections,
            "variant_shap_json": report.variant_shap_json,
            "resistance_shap_json": report.resistance_shap_json,
            "toxicity_shap_json": report.toxicity_shap_json,
            "llm_model_used": report.llm_model_used,
            "generation_duration_seconds": report.generation_duration_seconds,
            "generation_temperature": report.generation_temperature,
            "readability_score": report.readability_score,
            "medical_terminology_score": report.medical_terminology_score,
            "completeness_score": report.completeness_score,
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat(),
            "clinician_id": report.clinician_id
        }
    
    async def get_by_therapy_report_id(self, therapy_report_id: str) -> Optional[dict]:
        """Get narrative report by therapy report ID."""
        stmt = select(NarrativeReport).where(
            and_(
                NarrativeReport.therapy_report_id == therapy_report_id,
                NarrativeReport.deleted_at.is_(None)
            )
        ).order_by(desc(NarrativeReport.created_at))
        
        result = await self.db.execute(stmt)
        report = result.scalars().first()
        
        if not report:
            return None
        
        return await self.get_by_id(str(report.id))
    
    async def list_for_patient(
        self,
        patient_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[dict], int]:
        """List narrative reports for a patient."""
        
        # Count total
        count_stmt = select(sqlalchemy.func.count(NarrativeReport.id)).where(
            and_(
                NarrativeReport.patient_id == patient_id,
                NarrativeReport.deleted_at.is_(None)
            )
        )
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar() or 0
        
        # Get paginated results
        stmt = select(NarrativeReport).where(
            and_(
                NarrativeReport.patient_id == patient_id,
                NarrativeReport.deleted_at.is_(None)
            )
        ).order_by(desc(NarrativeReport.created_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        reports = result.scalars().all()
        
        reports_list = []
        for report in reports:
            report_dict = await self.get_by_id(str(report.id))
            if report_dict:
                reports_list.append(report_dict)
        
        return reports_list, total_count
    
    async def update_quality_scores(
        self,
        narrative_id: str,
        readability_score: Optional[float] = None,
        medical_terminology_score: Optional[float] = None,
        completeness_score: Optional[float] = None
    ) -> bool:
        """Update quality metrics for narrative."""
        
        update_data = {}
        if readability_score is not None:
            update_data["readability_score"] = readability_score
        if medical_terminology_score is not None:
            update_data["medical_terminology_score"] = medical_terminology_score
        if completeness_score is not None:
            update_data["completeness_score"] = completeness_score
        
        if not update_data:
            return False
        
        update_data["updated_at"] = datetime.utcnow()
        
        stmt = update(NarrativeReport).where(
            NarrativeReport.id == narrative_id
        ).values(**update_data)
        
        result = await self.db.execute(stmt)
        await self.db.flush()
        
        return result.rowcount > 0
    
    async def soft_delete(self, narrative_id: str) -> bool:
        """Soft delete a narrative report."""
        
        stmt = update(NarrativeReport).where(
            NarrativeReport.id == narrative_id
        ).values(
            deleted_at=datetime.utcnow()
        )
        
        result = await self.db.execute(stmt)
        await self.db.flush()
        
        return result.rowcount > 0
    
    async def get_statistics(self) -> dict:
        """Get statistics on narrative generation."""
        
        # Total narratives
        total_stmt = select(sqlalchemy.func.count(NarrativeReport.id)).where(
            NarrativeReport.deleted_at.is_(None)
        )
        total_result = await self.db.execute(total_stmt)
        total_count = total_result.scalar() or 0
        
        # Average generation time
        avg_time_stmt = select(
            sqlalchemy.func.avg(NarrativeReport.generation_duration_seconds)
        ).where(NarrativeReport.deleted_at.is_(None))
        avg_time_result = await self.db.execute(avg_time_stmt)
        avg_generation_time = avg_time_result.scalar() or 0
        
        # Average scores
        avg_readability_stmt = select(
            sqlalchemy.func.avg(NarrativeReport.readability_score)
        ).where(
            and_(
                NarrativeReport.deleted_at.is_(None),
                NarrativeReport.readability_score.isnot(None)
            )
        )
        avg_readability_result = await self.db.execute(avg_readability_stmt)
        avg_readability = avg_readability_result.scalar() or 0
        
        avg_completeness_stmt = select(
            sqlalchemy.func.avg(NarrativeReport.completeness_score)
        ).where(
            and_(
                NarrativeReport.deleted_at.is_(None),
                NarrativeReport.completeness_score.isnot(None)
            )
        )
        avg_completeness_result = await self.db.execute(avg_completeness_stmt)
        avg_completeness = avg_completeness_result.scalar() or 0
        
        # Models used
        models_stmt = select(
            NarrativeReport.llm_model_used,
            sqlalchemy.func.count(NarrativeReport.id).label("count")
        ).where(
            NarrativeReport.deleted_at.is_(None)
        ).group_by(NarrativeReport.llm_model_used)
        
        models_result = await self.db.execute(models_stmt)
        models_used = {row[0]: row[1] for row in models_result.fetchall()}
        
        return {
            "total_narratives": total_count,
            "avg_generation_seconds": float(avg_generation_time),
            "avg_readability_score": float(avg_readability),
            "avg_completeness_score": float(avg_completeness),
            "models_used": models_used
        }
    
    async def get_recent_narratives(self, limit: int = 10) -> List[dict]:
        """Get recently generated narratives."""
        
        stmt = select(NarrativeReport).where(
            NarrativeReport.deleted_at.is_(None)
        ).order_by(desc(NarrativeReport.created_at)).limit(limit)
        
        result = await self.db.execute(stmt)
        reports = result.scalars().all()
        
        narratives = []
        for report in reports:
            narrative_dict = await self.get_by_id(str(report.id))
            if narrative_dict:
                narratives.append(narrative_dict)
        
        return narratives
