"""Repository layer for omics data persistence."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import logging
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base, mapped_column
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import uuid

logger = logging.getLogger(__name__)

Base = declarative_base()


class RNAResult(Base):
    """SQLAlchemy model for RNA-seq results."""
    __tablename__ = 'rna_results'

    id: uuid.UUID = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: uuid.UUID = mapped_column(PG_UUID(as_uuid=True), ForeignKey('patients.patient_id'), nullable=False, index=True)
    gene_id: str = mapped_column(String(50), nullable=False)
    gene_name: str = mapped_column(String(255), nullable=False)
    log2_fold_change: float = mapped_column(Float, nullable=False)
    p_value: float = mapped_column(Float, nullable=False)
    padj: float = mapped_column(Float, nullable=False, index=True)
    base_mean: Optional[float] = mapped_column(Float, nullable=True)
    case_mean: Optional[float] = mapped_column(Float, nullable=True)
    control_mean: Optional[float] = mapped_column(Float, nullable=True)
    significance_flag: Optional[str] = mapped_column(String(20), nullable=True)
    effect_size: Optional[float] = mapped_column(Float, nullable=True)
    expression_level: Optional[str] = mapped_column(String(20), nullable=True)
    transcript_biotype: Optional[str] = mapped_column(String(50), nullable=True)
    go_annotations: Optional[Dict] = mapped_column(JSONB, nullable=True)
    pathway_associations: Optional[Dict] = mapped_column(JSONB, nullable=True)
    clinical_relevance: Optional[str] = mapped_column(Text, nullable=True)
    metadata: Optional[Dict] = mapped_column(JSONB, nullable=True)
    created_at: datetime = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: datetime = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Optional[datetime] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class ProteinResult(Base):
    """SQLAlchemy model for proteomics results."""
    __tablename__ = 'protein_results'

    id: uuid.UUID = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: uuid.UUID = mapped_column(PG_UUID(as_uuid=True), ForeignKey('patients.patient_id'), nullable=False, index=True)
    protein_id: str = mapped_column(String(100), nullable=False, index=True)
    protein_name: str = mapped_column(String(255), nullable=False)
    gene_name: Optional[str] = mapped_column(String(100), nullable=True, index=True)
    uniprot_id: Optional[str] = mapped_column(String(10), nullable=True, index=True)
    lfq_intensity: float = mapped_column(Float, nullable=False)
    log2_intensity: float = mapped_column(Float, nullable=False, index=True)
    peptide_count: Optional[int] = mapped_column(Integer, nullable=True)
    unique_peptides: Optional[int] = mapped_column(Integer, nullable=True)
    razor_peptides: Optional[int] = mapped_column(Integer, nullable=True)
    sequence_coverage: Optional[float] = mapped_column(Float, nullable=True)
    molecular_weight: Optional[float] = mapped_column(Float, nullable=True)
    protein_probability: Optional[float] = mapped_column(Float, nullable=True)
    intensity_ratio: Optional[float] = mapped_column(Float, nullable=True)
    fold_change: Optional[float] = mapped_column(Float, nullable=True, index=True)
    protein_class: Optional[str] = mapped_column(String(50), nullable=True, index=True)
    pathway_associations: Optional[Dict] = mapped_column(JSONB, nullable=True)
    post_modifications: Optional[Dict] = mapped_column(JSONB, nullable=True)
    tissue_expression: Optional[Dict] = mapped_column(JSONB, nullable=True)
    disease_associations: Optional[Dict] = mapped_column(JSONB, nullable=True)
    drug_target_info: Optional[Dict] = mapped_column(JSONB, nullable=True)
    clinical_significance: Optional[str] = mapped_column(Text, nullable=True)
    metadata: Optional[Dict] = mapped_column(JSONB, nullable=True)
    created_at: datetime = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: datetime = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Optional[datetime] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class OmicsRepository:
    """Repository for omics data operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with async session."""
        self.session = session
        self.logger = logging.getLogger(__name__)

    # ==================== RNA OPERATIONS ====================

    async def create_rna_results(self, results: List[Dict[str, Any]]) -> int:
        """
        Batch create RNA-seq results.

        Args:
            results: List of RNA result dictionaries

        Returns:
            Number of rows inserted
        """
        try:
            rna_objs = [RNAResult(**result) for result in results]
            self.session.add_all(rna_objs)
            await self.session.flush()
            self.logger.info(f"Created {len(rna_objs)} RNA results")
            return len(rna_objs)
        except Exception as e:
            self.logger.error(f"Error creating RNA results: {e}")
            raise

    async def get_rna_results_by_patient(self, patient_id: UUID, limit: Optional[int] = None) -> List[RNAResult]:
        """Get RNA results for a patient."""
        query = select(RNAResult).where(
            and_(RNAResult.patient_id == patient_id, RNAResult.deleted_at.is_(None))
        )
        if limit:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_significant_genes(self, patient_id: UUID, padj_threshold: float = 0.05) -> List[RNAResult]:
        """Get significantly differentially expressed genes."""
        query = select(RNAResult).where(
            and_(
                RNAResult.patient_id == patient_id,
                RNAResult.padj < padj_threshold,
                RNAResult.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_upregulated_genes(self, patient_id: UUID, lfc_threshold: float = 1.0) -> List[RNAResult]:
        """Get upregulated genes."""
        query = select(RNAResult).where(
            and_(
                RNAResult.patient_id == patient_id,
                RNAResult.log2_fold_change > lfc_threshold,
                RNAResult.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_downregulated_genes(self, patient_id: UUID, lfc_threshold: float = 1.0) -> List[RNAResult]:
        """Get downregulated genes."""
        query = select(RNAResult).where(
            and_(
                RNAResult.patient_id == patient_id,
                RNAResult.log2_fold_change < -lfc_threshold,
                RNAResult.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    # ==================== PROTEOMICS OPERATIONS ====================

    async def create_protein_results(self, results: List[Dict[str, Any]]) -> int:
        """
        Batch create protein results.

        Args:
            results: List of protein result dictionaries

        Returns:
            Number of rows inserted
        """
        try:
            protein_objs = [ProteinResult(**result) for result in results]
            self.session.add_all(protein_objs)
            await self.session.flush()
            self.logger.info(f"Created {len(protein_objs)} protein results")
            return len(protein_objs)
        except Exception as e:
            self.logger.error(f"Error creating protein results: {e}")
            raise

    async def get_protein_results_by_patient(self, patient_id: UUID, limit: Optional[int] = None) -> List[ProteinResult]:
        """Get protein results for a patient."""
        query = select(ProteinResult).where(
            and_(ProteinResult.patient_id == patient_id, ProteinResult.deleted_at.is_(None))
        )
        if limit:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_drug_target_proteins(self, patient_id: UUID) -> List[ProteinResult]:
        """Get proteins that are known drug targets."""
        query = select(ProteinResult).where(
            and_(
                ProteinResult.patient_id == patient_id,
                ProteinResult.drug_target_info.isnot(None),
                ProteinResult.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_enzyme_proteins(self, patient_id: UUID) -> List[ProteinResult]:
        """Get proteins classified as enzymes."""
        query = select(ProteinResult).where(
            and_(
                ProteinResult.patient_id == patient_id,
                ProteinResult.protein_class == 'enzyme',
                ProteinResult.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_receptors(self, patient_id: UUID) -> List[ProteinResult]:
        """Get proteins classified as receptors."""
        query = select(ProteinResult).where(
            and_(
                ProteinResult.patient_id == patient_id,
                ProteinResult.protein_class == 'receptor',
                ProteinResult.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    # ==================== STATISTICS ====================

    async def count_rna_results(self, patient_id: Optional[UUID] = None) -> int:
        """Count RNA results."""
        query = select(func.count(RNAResult.id)).where(RNAResult.deleted_at.is_(None))
        if patient_id:
            query = query.where(RNAResult.patient_id == patient_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_protein_results(self, patient_id: Optional[UUID] = None) -> int:
        """Count protein results."""
        query = select(func.count(ProteinResult.id)).where(ProteinResult.deleted_at.is_(None))
        if patient_id:
            query = query.where(ProteinResult.patient_id == patient_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_patients_with_rna(self) -> int:
        """Count patients with RNA-seq data."""
        query = select(func.count(func.distinct(RNAResult.patient_id))).where(RNAResult.deleted_at.is_(None))
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def count_patients_with_proteomics(self) -> int:
        """Count patients with proteomics data."""
        query = select(func.count(func.distinct(ProteinResult.patient_id))).where(ProteinResult.deleted_at.is_(None))
        result = await self.session.execute(query)
        return result.scalar() or 0

    # ==================== SOFT DELETE ====================

    async def soft_delete_rna_results(self, patient_id: UUID) -> int:
        """Soft delete RNA results for a patient."""
        query = select(RNAResult).where(
            and_(RNAResult.patient_id == patient_id, RNAResult.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        rows = result.scalars().all()
        for row in rows:
            row.deleted_at = datetime.utcnow()
        await self.session.flush()
        return len(rows)

    async def soft_delete_protein_results(self, patient_id: UUID) -> int:
        """Soft delete protein results for a patient."""
        query = select(ProteinResult).where(
            and_(ProteinResult.patient_id == patient_id, ProteinResult.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        rows = result.scalars().all()
        for row in rows:
            row.deleted_at = datetime.utcnow()
        await self.session.flush()
        return len(rows)
