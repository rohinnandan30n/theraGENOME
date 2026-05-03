"""
Therapy Report Repository
CRUD operations for therapy_reports table
"""

import asyncio
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
import logging

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, update, delete, desc
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    AsyncSession = None
    logging.warning("SQLAlchemy not available - database operations will be limited")

logger = logging.getLogger(__name__)


class TherapyReportRepository:
    """Repository for therapy_reports table operations"""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session
    
    async def create_report(self, report_data: Dict) -> Optional[UUID]:
        """
        Create a new therapy report in the database.
        
        Args:
            report_data: Dictionary with all report fields
            
        Returns:
            report_id (UUID) if successful, None otherwise
        """
        if not SQLALCHEMY_AVAILABLE or not self.db_session:
            logger.warning("Database session not available - report not persisted")
            return report_data.get('report_id')
        
        try:
            # Build INSERT query
            query = """
                INSERT INTO therapy_reports (
                    report_id, patient_id, sample_id,
                    variant_summary, variant_classification, variant_confidence, variant_result_id,
                    resistance_summary, predicted_phenotype, resistance_confidence, resistance_result_id,
                    toxicity_summary, toxicity_risk, toxicity_confidence, drug_interactions,
                    recommended_drug, alternative_drugs, recommendation_confidence, recommendation_rationale,
                    drug_candidates, status, variant_service_status, resistance_service_status,
                    toxicity_service_status, variant_latency_ms, resistance_latency_ms, toxicity_latency_ms,
                    error_messages, created_by, clinician_id, created_at, updated_at
                ) VALUES (
                    :report_id, :patient_id, :sample_id,
                    :variant_summary, :variant_classification, :variant_confidence, :variant_result_id,
                    :resistance_summary, :predicted_phenotype, :resistance_confidence, :resistance_result_id,
                    :toxicity_summary, :toxicity_risk, :toxicity_confidence, :drug_interactions,
                    :recommended_drug, :alternative_drugs, :recommendation_confidence, :recommendation_rationale,
                    :drug_candidates, :status, :variant_service_status, :resistance_service_status,
                    :toxicity_service_status, :variant_latency_ms, :resistance_latency_ms, :toxicity_latency_ms,
                    :error_messages, :created_by, :clinician_id, :created_at, :updated_at
                )
            """
            
            await self.db_session.execute(query, report_data)
            await self.db_session.commit()
            
            logger.info(f"Created therapy report {report_data['report_id']}")
            return report_data['report_id']
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error creating therapy report: {str(e)}")
            return None
    
    async def get_report_by_id(self, report_id: UUID) -> Optional[Dict]:
        """
        Retrieve a therapy report by its ID.
        
        Args:
            report_id: Report UUID
            
        Returns:
            Report dictionary or None
        """
        if not SQLALCHEMY_AVAILABLE or not self.db_session:
            return None
        
        try:
            query = """
                SELECT * FROM therapy_reports 
                WHERE report_id = :report_id AND deleted_at IS NULL
            """
            
            result = await self.db_session.execute(query, {"report_id": report_id})
            row = result.first()
            
            if row:
                return dict(row._mapping)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving therapy report {report_id}: {str(e)}")
            return None
    
    async def get_reports_by_patient(
        self, 
        patient_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict]:
        """
        Get all therapy reports for a patient.
        
        Args:
            patient_id: Patient UUID
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of report dictionaries
        """
        if not SQLALCHEMY_AVAILABLE or not self.db_session:
            return []
        
        try:
            query = """
                SELECT * FROM therapy_reports 
                WHERE patient_id = :patient_id AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            result = await self.db_session.execute(
                query, 
                {
                    "patient_id": patient_id, 
                    "limit": limit, 
                    "offset": offset
                }
            )
            
            return [dict(row._mapping) for row in result.fetchall()]
            
        except Exception as e:
            logger.error(f"Error retrieving reports for patient {patient_id}: {str(e)}")
            return []
    
    async def update_report(self, report_id: UUID, updates: Dict) -> bool:
        """
        Update a therapy report.
        
        Args:
            report_id: Report UUID
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if not SQLALCHEMY_AVAILABLE or not self.db_session:
            return False
        
        try:
            updates['updated_at'] = datetime.utcnow()
            
            # Build dynamic UPDATE query
            set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
            query = f"""
                UPDATE therapy_reports 
                SET {set_clause}
                WHERE report_id = :report_id
            """
            updates['report_id'] = report_id
            
            result = await self.db_session.execute(query, updates)
            await self.db_session.commit()
            
            logger.info(f"Updated therapy report {report_id}")
            return result.rowcount > 0
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error updating therapy report {report_id}: {str(e)}")
            return False
    
    async def soft_delete_report(self, report_id: UUID) -> bool:
        """
        Soft delete a therapy report.
        
        Args:
            report_id: Report UUID
            
        Returns:
            True if successful, False otherwise
        """
        if not SQLALCHEMY_AVAILABLE or not self.db_session:
            return False
        
        return await self.update_report(report_id, {'deleted_at': datetime.utcnow()})
    
    async def get_recent_reports(
        self, 
        limit: int = 10, 
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        Get recent therapy reports, optionally filtered by status.
        
        Args:
            limit: Number of recent reports to retrieve
            status: Filter by status (complete/partial/error/timeout)
            
        Returns:
            List of report dictionaries
        """
        if not SQLALCHEMY_AVAILABLE or not self.db_session:
            return []
        
        try:
            query = """
                SELECT * FROM therapy_reports 
                WHERE deleted_at IS NULL
            """
            params = {}
            
            if status:
                query += " AND status = :status"
                params['status'] = status
            
            query += " ORDER BY created_at DESC LIMIT :limit"
            params['limit'] = limit
            
            result = await self.db_session.execute(query, params)
            
            return [dict(row._mapping) for row in result.fetchall()]
            
        except Exception as e:
            logger.error(f"Error retrieving recent reports: {str(e)}")
            return []
    
    async def get_statistics(self) -> Dict:
        """
        Get statistics about therapy reports.
        
        Returns:
            Dictionary with report statistics
        """
        if not SQLALCHEMY_AVAILABLE or not self.db_session:
            return {}
        
        try:
            query = """
                SELECT 
                    COUNT(*) as total_reports,
                    COUNT(CASE WHEN status = 'complete' THEN 1 END) as complete_reports,
                    COUNT(CASE WHEN status = 'partial' THEN 1 END) as partial_reports,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_reports,
                    COUNT(CASE WHEN status = 'timeout' THEN 1 END) as timeout_reports,
                    ROUND(AVG(COALESCE(variant_latency_ms, 0))::numeric, 2) as avg_variant_latency_ms,
                    ROUND(AVG(COALESCE(resistance_latency_ms, 0))::numeric, 2) as avg_resistance_latency_ms,
                    ROUND(AVG(COALESCE(toxicity_latency_ms, 0))::numeric, 2) as avg_toxicity_latency_ms,
                    ROUND(AVG(recommendation_confidence), 3) as avg_recommendation_confidence
                FROM therapy_reports 
                WHERE deleted_at IS NULL
            """
            
            result = await self.db_session.execute(query)
            row = result.first()
            
            if row:
                return dict(row._mapping)
            return {}
            
        except Exception as e:
            logger.error(f"Error retrieving statistics: {str(e)}")
            return {}
