"""
Pytest configuration and fixtures for Dev 3 tests.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_async_session():
    """Mock AsyncSession for database tests."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.setex = AsyncMock()
    client.delete = AsyncMock()
    client.flushdb = AsyncMock()
    return client


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver."""
    driver = AsyncMock()
    return driver


@pytest.fixture
def sample_drug_data():
    """Sample drug data for testing."""
    return {
        "id": 1,
        "name": "aspirin",
        "drugbank_id": "DB00945",
        "description": "Acetylsalicylic acid",
        "category": "NSAID",
    }


@pytest.fixture
def sample_pgx_data():
    """Sample PGx data for testing."""
    return {
        "id": 1,
        "gene": "CYP2C9",
        "drug_id": 1,
        "recommendation": "Reduce dose by 30-50% for poor metabolizers",
        "evidence_level": "1A",
        "phenotype_categories": ["Poor metabolizer"],
        "source": "PharmGKB",
    }


@pytest.fixture
def sample_ddi_data():
    """Sample DDI data for testing."""
    return {
        "id": 1,
        "drug_a_id": 1,
        "drug_b_id": 2,
        "interaction_type": "Pharmacodynamic",
        "severity": "Major",
        "description": "Increases anticoagulant effect, raising bleeding risk",
        "source": "local_knowledge_base",
    }


@pytest.fixture
def sample_adverse_event_data():
    """Sample adverse event data for testing."""
    return {
        "id": 1,
        "drug_id": 1,
        "event_type": "Gastrointestinal hemorrhage",
        "event_count": 150,
        "seriousness_level": "serious",
        "source": "FDA-FAERS",
    }
