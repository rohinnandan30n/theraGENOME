"""
Drug safety specific database repository for drug, PGx, DDI, and adverse event queries.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from src.db.repository import BaseRepository
from src.schemas.drug_schema import Drug, PGxRecommendation, DrugDrugInteraction, AdverseEvent


class DrugRepository(BaseRepository[Drug]):
    """Repository for drug information."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Drug)

    async def get_by_name(self, name: str) -> Optional[Drug]:
        """Get drug by name."""
        query = select(self.model_class).where(self.model_class.name.ilike(name))
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_drugbank_id(self, drugbank_id: str) -> Optional[Drug]:
        """Get drug by DrugBank ID."""
        query = select(self.model_class).where(self.model_class.drugbank_id == drugbank_id)
        result = await self.session.execute(query)
        return result.scalars().first()


class PGxRepository(BaseRepository[PGxRecommendation]):
    """Repository for pharmacogenomics recommendations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PGxRecommendation)

    async def get_by_gene_and_drug(self, gene: str, drug_id: int) -> Optional[PGxRecommendation]:
        """Get PGx recommendation by gene and drug ID."""
        query = select(self.model_class).where(
            and_(
                self.model_class.gene == gene,
                self.model_class.drug_id == drug_id
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_gene(self, gene: str) -> List[PGxRecommendation]:
        """Get all PGx recommendations for a gene."""
        query = select(self.model_class).where(self.model_class.gene == gene)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_drug_id(self, drug_id: int) -> List[PGxRecommendation]:
        """Get all PGx recommendations for a drug."""
        query = select(self.model_class).where(self.model_class.drug_id == drug_id)
        result = await self.session.execute(query)
        return result.scalars().all()


class DDIRepository(BaseRepository[DrugDrugInteraction]):
    """Repository for drug-drug interactions."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DrugDrugInteraction)

    async def get_by_drug_pair(
        self, drug_a_id: int, drug_b_id: int
    ) -> Optional[DrugDrugInteraction]:
        """Get DDI between two drugs (order-independent)."""
        query = select(self.model_class).where(
            and_(
                self.model_class.drug_a_id.in_([drug_a_id, drug_b_id]),
                self.model_class.drug_b_id.in_([drug_a_id, drug_b_id]),
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_interactions_for_drug(self, drug_id: int) -> List[DrugDrugInteraction]:
        """Get all interactions involving a drug."""
        query = select(self.model_class).where(
            (self.model_class.drug_a_id == drug_id) | (self.model_class.drug_b_id == drug_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()


class AdverseEventRepository(BaseRepository[AdverseEvent]):
    """Repository for adverse events."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AdverseEvent)

    async def get_by_drug_id(self, drug_id: int) -> List[AdverseEvent]:
        """Get all adverse events for a drug."""
        query = select(self.model_class).where(self.model_class.drug_id == drug_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_event_type(self, event_type: str) -> List[AdverseEvent]:
        """Get adverse events by type."""
        query = select(self.model_class).where(
            self.model_class.event_type.ilike(f"%{event_type}%")
        )
        result = await self.session.execute(query)
        return result.scalars().all()
