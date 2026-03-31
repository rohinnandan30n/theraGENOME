"""
Unit tests for database repositories and models.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select
from src.db.drug_safety_repository import (
    DrugRepository,
    PGxRepository,
    DDIRepository,
    AdverseEventRepository,
)
from src.schemas.drug_schema import Drug, PGxRecommendation, DrugDrugInteraction, AdverseEvent


class TestDrugRepository:
    """Test suite for Drug repository."""

    @pytest.mark.asyncio
    async def test_get_by_name(self):
        """Test retrieving drug by name."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = Drug(
            id=1, name="aspirin", drugbank_id="DB00945"
        )

        mock_session.execute.return_value = mock_result

        repo = DrugRepository(mock_session)
        result = await repo.get_by_name("aspirin")

        assert result.id == 1
        assert result.name == "aspirin"

    @pytest.mark.asyncio
    async def test_get_by_drugbank_id(self):
        """Test retrieving drug by DrugBank ID."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = Drug(
            id=1, name="aspirin", drugbank_id="DB00945"
        )

        mock_session.execute.return_value = mock_result

        repo = DrugRepository(mock_session)
        result = await repo.get_by_drugbank_id("DB00945")

        assert result.drugbank_id == "DB00945"


class TestPGxRepository:
    """Test suite for PGx repository."""

    @pytest.mark.asyncio
    async def test_get_by_gene_and_drug(self):
        """Test retrieving PGx recommendation by gene and drug."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = PGxRecommendation(
            id=1,
            gene="CYP2C9",
            drug_id=1,
            recommendation="Reduce dose by 30-50%",
            evidence_level="1A",
        )

        mock_session.execute.return_value = mock_result

        repo = PGxRepository(mock_session)
        result = await repo.get_by_gene_and_drug("CYP2C9", 1)

        assert result.gene == "CYP2C9"
        assert result.drug_id == 1

    @pytest.mark.asyncio
    async def test_get_by_gene(self):
        """Test retrieving all PGx recommendations for a gene."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        pgx_list = [
            PGxRecommendation(
                id=1,
                gene="CYP2C9",
                drug_id=1,
                recommendation="Rec 1",
                evidence_level="1A",
            ),
            PGxRecommendation(
                id=2,
                gene="CYP2C9",
                drug_id=2,
                recommendation="Rec 2",
                evidence_level="2B",
            ),
        ]
        mock_result.scalars.return_value.all.return_value = pgx_list

        mock_session.execute.return_value = mock_result

        repo = PGxRepository(mock_session)
        results = await repo.get_by_gene("CYP2C9")

        assert len(results) == 2
        assert all(r.gene == "CYP2C9" for r in results)


class TestDDIRepository:
    """Test suite for DDI repository."""

    @pytest.mark.asyncio
    async def test_get_by_drug_pair(self):
        """Test retrieving DDI between two drugs."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = DrugDrugInteraction(
            id=1,
            drug_a_id=1,
            drug_b_id=2,
            interaction_type="Pharmacodynamic",
            severity="Major",
        )

        mock_session.execute.return_value = mock_result

        repo = DDIRepository(mock_session)
        result = await repo.get_by_drug_pair(1, 2)

        assert result.severity == "Major"

    @pytest.mark.asyncio
    async def test_get_interactions_for_drug(self):
        """Test retrieving all interactions for a drug."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        interactions = [
            DrugDrugInteraction(
                id=1,
                drug_a_id=1,
                drug_b_id=2,
                interaction_type="Type 1",
                severity="Major",
            ),
            DrugDrugInteraction(
                id=2,
                drug_a_id=1,
                drug_b_id=3,
                interaction_type="Type 2",
                severity="Moderate",
            ),
        ]
        mock_result.scalars.return_value.all.return_value = interactions

        mock_session.execute.return_value = mock_result

        repo = DDIRepository(mock_session)
        results = await repo.get_interactions_for_drug(1)

        assert len(results) == 2


class TestAdverseEventRepository:
    """Test suite for AdverseEvent repository."""

    @pytest.mark.asyncio
    async def test_get_by_drug_id(self):
        """Test retrieving adverse events for a drug."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        events = [
            AdverseEvent(
                id=1,
                drug_id=1,
                event_type="Gastrointestinal hemorrhage",
                event_count=150,
                seriousness_level="serious",
            ),
            AdverseEvent(
                id=2,
                drug_id=1,
                event_type="Allergic reaction",
                event_count=45,
                seriousness_level="non-serious",
            ),
        ]
        mock_result.scalars.return_value.all.return_value = events

        mock_session.execute.return_value = mock_result

        repo = AdverseEventRepository(mock_session)
        results = await repo.get_by_drug_id(1)

        assert len(results) == 2
        assert results[0].event_count == 150

    @pytest.mark.asyncio
    async def test_get_by_event_type(self):
        """Test retrieving adverse events by type."""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        events = [
            AdverseEvent(
                id=1,
                drug_id=1,
                event_type="Gastrointestinal hemorrhage",
                event_count=150,
            ),
            AdverseEvent(
                id=2,
                drug_id=2,
                event_type="Gastrointestinal disorder",
                event_count=200,
            ),
        ]
        mock_result.scalars.return_value.all.return_value = events

        mock_session.execute.return_value = mock_result

        repo = AdverseEventRepository(mock_session)
        results = await repo.get_by_event_type("Gastrointestinal")

        assert len(results) == 2
