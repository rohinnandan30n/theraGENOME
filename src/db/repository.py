import uuid
from datetime import datetime
from typing import List, Dict, Any
from src.db.connection import db
import logging

logger = logging.getLogger(__name__)


class VariantRepository:
    @staticmethod
    def create_ingestion_job(filename: str) -> str:
        """Create a new ingestion job and return job ID"""
        job_id = str(uuid.uuid4())
        
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ingestion_jobs (id, filename, status)
                VALUES (%s, %s, %s)
                """,
                (job_id, filename, 'PENDING')
            )
        
        logger.info(f"Created ingestion job: {job_id}")
        return job_id

    @staticmethod
    def insert_variants(job_id: str, variants: List[Dict[str, Any]]) -> int:
        """Insert parsed variants into database"""
        if not variants:
            return 0
        
        with db.get_cursor() as cursor:
            for variant in variants:
                cursor.execute(
                    """
                    INSERT INTO variants (job_id, chrom, pos, ref, alt, qual, info)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        job_id,
                        variant.get('chrom'),
                        variant.get('pos'),
                        variant.get('ref'),
                        variant.get('alt'),
                        variant.get('qual'),
                        variant.get('info')
                    )
                )
        
        logger.info(f"Inserted {len(variants)} variants for job {job_id}")
        return len(variants)

    @staticmethod
    def update_job_status(job_id: str, status: str, variant_count: int = None):
        """Update ingestion job status"""
        with db.get_cursor() as cursor:
            if variant_count is not None:
                cursor.execute(
                    """
                    UPDATE ingestion_jobs
                    SET status = %s, variant_count = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (status, variant_count, job_id)
                )
            else:
                cursor.execute(
                    """
                    UPDATE ingestion_jobs
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (status, job_id)
                )
        
        logger.info(f"Updated job {job_id} status to {status}")

    @staticmethod
    def get_job(job_id: str) -> Dict[str, Any]:
        """Get ingestion job details"""
        with db.get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM ingestion_jobs WHERE id = %s",
                (job_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def get_variants_by_job(job_id: str) -> List[Dict[str, Any]]:
        """Get all variants for a specific job"""
        with db.get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM variants WHERE job_id = %s",
                (job_id,)
            )
            return cursor.fetchall()
