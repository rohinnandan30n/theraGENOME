"""
Pytest configuration and shared fixtures for test suite.

Provides database session fixtures, mock clients, and common test utilities.
Uses in-memory SQLite for testing to avoid PostgreSQL dependency.
"""

import pytest
import sys
import os
from typing import Generator
from unittest.mock import Mock, AsyncMock, patch
import sqlite3

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient

# Import the application
from src.api.main import app


# Simple mock class for HTTPAuthCredentials
class HTTPAuthCredentials:
    """Mock HTTPAuthCredentials for testing."""
    def __init__(self, scheme: str, credentials: str):
        self.scheme = scheme
        self.credentials = credentials


# SQLite In-Memory Database Configuration for Testing
TEST_DATABASE_URL = "sqlite:///:memory:"


class SQLiteTestConnection:
    """Mock database connection using SQLite for testing."""
    
    def __init__(self, db_connection):
        """Initialize with in-memory SQLite connection."""
        self.db_connection = db_connection
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema for testing."""
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        
        # Create SQLite-compatible schema
        schema_sql = """
        -- Variant schema for genomic data storage
        CREATE TABLE IF NOT EXISTS variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL UNIQUE,
            chrom VARCHAR(20) NOT NULL,
            pos INTEGER NOT NULL,
            ref VARCHAR(1000) NOT NULL,
            alt VARCHAR(1000) NOT NULL,
            qual FLOAT,
            info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS ingestion_jobs (
            id TEXT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'PENDING',
            variant_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Model performance tracking table
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variant_id VARCHAR(255),
            model_version VARCHAR(50) NOT NULL,
            predicted_label VARCHAR(50) NOT NULL,
            true_label VARCHAR(50),
            confidence FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_created_at ON model_performance(created_at);
        CREATE INDEX IF NOT EXISTS idx_model_version ON model_performance(model_version);
        CREATE INDEX IF NOT EXISTS idx_variant_id ON model_performance(variant_id);
        """
        
        for statement in schema_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        conn.commit()
        self.connection = conn
    
    def get_connection(self):
        """Get SQLite connection."""
        return self.connection
    
    def get_cursor(self, commit=True):
        """Context manager for database operations using SQLite."""
        class CursorContext:
            def __init__(self, connection, commit_flag):
                self.connection = connection
                self.cursor = connection.cursor()
                self.commit_flag = commit_flag
            
            def __enter__(self):
                return self.cursor
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None and self.commit_flag:
                    self.connection.commit()
                else:
                    self.connection.rollback()
        
        return CursorContext(self.connection, commit)


# Create a global in-memory SQLite test database
_test_db = None


def get_test_db():
    """Get or create test database connection."""
    global _test_db
    if _test_db is None:
        # Create actual SQLite connection
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        
        # Create SQLite-compatible schema
        schema_sql = """
        CREATE TABLE IF NOT EXISTS variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL UNIQUE,
            chrom VARCHAR(20) NOT NULL,
            pos INTEGER NOT NULL,
            ref VARCHAR(1000) NOT NULL,
            alt VARCHAR(1000) NOT NULL,
            qual FLOAT,
            info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS ingestion_jobs (
            id TEXT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'PENDING',
            variant_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variant_id VARCHAR(255),
            model_version VARCHAR(50) NOT NULL,
            predicted_label VARCHAR(50) NOT NULL,
            true_label VARCHAR(50),
            confidence FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_created_at ON model_performance(created_at);
        CREATE INDEX IF NOT EXISTS idx_model_version ON model_performance(model_version);
        CREATE INDEX IF NOT EXISTS idx_variant_id ON model_performance(variant_id);
        """
        
        for statement in schema_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        conn.commit()
        
        # Create wrapper object with query translation
        class ConvertingCursor:
            """Wrapper cursor that converts PostgreSQL SQL to SQLite SQL."""
            def __init__(self, sqlite_cursor):
                self._cursor = sqlite_cursor
            
            def _convert_query(self, query):
                """Convert PostgreSQL query syntax to SQLite syntax."""
                import re
                # Replace %s placeholders with ?
                converted = query.replace('%s', '?')
                # Remove RETURNING clauses (SQLite doesn't fully support them)
                converted = re.sub(r'\s+RETURNING\s+.*$', '', converted, flags=re.IGNORECASE | re.MULTILINE)
                return converted
            
            def execute(self, query, args=None):
                """Execute query with automatic SQL conversion."""
                converted_query = self._convert_query(query)
                if args:
                    return self._cursor.execute(converted_query, args)
                else:
                    return self._cursor.execute(converted_query)
            
            def executemany(self, query, args):
                """Execute many queries with automatic SQL conversion."""
                converted_query = self._convert_query(query)
                return self._cursor.executemany(converted_query, args)
            
            def fetchone(self):
                """Fetch one row from the result set."""
                row = self._cursor.fetchone()
                if row is None:
                    return None
                # Convert to dict-like object for compatibility with psycopg2 RealDictCursor
                return dict(row) if hasattr(row, 'keys') else row
            
            def fetchall(self):
                """Fetch all rows from the result set."""
                rows = self._cursor.fetchall()
                # Convert rows to dict-like objects
                return [dict(row) if hasattr(row, 'keys') else row for row in rows]
            
            def __getattr__(self, name):
                """Delegate other attributes to the underlying cursor."""
                return getattr(self._cursor, name)
        
        class TestDB:
            def __init__(self, connection):
                self.conn = connection
            
            def get_cursor(self, commit=True):
                class CursorContext:
                    def __init__(self, conn, commit_flag):
                        self.connection = conn
                        self.sqlite_cursor = conn.cursor()
                        self.sqlite_cursor.row_factory = sqlite3.Row  # Enable column names
                        self.cursor = ConvertingCursor(self.sqlite_cursor)
                        self.commit_flag = commit_flag
                    
                    def __enter__(self):
                        return self.cursor
                    
                    def __exit__(self, exc_type, exc_val, exc_tb):
                        if exc_type is None and self.commit_flag:
                            self.connection.commit()
                        else:
                            self.connection.rollback()
                
                return CursorContext(self.conn, commit)
        
        _test_db = TestDB(conn)
    
    return _test_db


@pytest.fixture(scope="session", autouse=True)
def patch_db_for_tests(db_engine):
    """
    Automatically patch the global db instance for all tests.
    This ensures all database operations use SQLite instead of PostgreSQL.
    """
    import src.db.connection as connection_module
    
    # Replace the global db instance with our test database
    connection_module.db = db_engine
    
    yield
    
    # Cleanup is handled by SQLite closing


@pytest.fixture(scope="session", autouse=True)
def patch_cache_for_tests():
    """
    Automatically patch the cache layer for all tests.
    Uses in-memory cache so tests never require a real Redis server.
    """
    from src.cache.redis_cache import InMemoryCache
    import src.cache.redis_cache as cache_module
    
    # Create in-memory cache instance
    test_cache = InMemoryCache()
    
    # Replace the global cache instance
    cache_module._cache_instance = test_cache
    
    # Also patch the get_cache function to return our test cache
    original_get_cache = cache_module.get_cache
    
    def mock_get_cache():
        return test_cache
    
    cache_module.get_cache = mock_get_cache
    
    yield
    
    # Restore original function
    cache_module.get_cache = original_get_cache


@pytest.fixture(scope="session")
def db_engine():
    """Create in-memory SQLite test database engine."""
    return get_test_db()


@pytest.fixture
def db_session(db_engine):
    """
    Create a fresh database session for each test.
    Uses the in-memory SQLite database.
    
    Yields:
        Database cursor for test
    """
    with db_engine.get_cursor(commit=True) as cursor:
        yield cursor


@pytest.fixture
def test_client() -> TestClient:
    """
    Create test client for FastAPI application.
    Uses the patched SQLite database from patch_db_for_tests fixture.
    
    Returns:
        FastAPI test client with in-memory SQLite database
    """
    return TestClient(app)


@pytest.fixture
def mock_admin_token() -> str:
    """
    Create mock admin JWT token for testing.
    
    Returns:
        Bearer token string
    """
    return "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImlkIjoxfQ.mock"


@pytest.fixture
def mock_user_token() -> str:
    """
    Create mock user (non-admin) JWT token for testing.
    
    Returns:
        Bearer token string
    """
    return "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyIiwicm9sZSI6ImNsaW5pY2lhbiIsImlkIjoyfQ.mock"


@pytest.fixture
def valid_credentials() -> HTTPAuthCredentials:
    """
    Create valid HTTP Bearer credentials.
    
    Returns:
        HTTPAuthCredentials with valid token format
    """
    return HTTPAuthCredentials(
        scheme="bearer",
        credentials="header.payload.signature"
    )


@pytest.fixture
def invalid_credentials() -> HTTPAuthCredentials:
    """
    Create invalid HTTP Bearer credentials.
    
    Returns:
        HTTPAuthCredentials with invalid token format
    """
    return HTTPAuthCredentials(
        scheme="bearer",
        credentials="invalid_token"
    )


@pytest.fixture
def therapist_data() -> dict:
    """
    Provide sample therapist data for testing.
    
    Returns:
        Dictionary with therapist information
    """
    return {
        "name": "Dr. Test Therapist",
        "email": "test.therapist@example.com",
        "license_no": "TH-TEST-001",
        "specialization": "Test Therapy",
        "status": "active"
    }


@pytest.fixture
def multiple_therapists() -> list:
    """
    Provide sample data for multiple therapists.
    
    Returns:
        List of therapist dictionaries
    """
    return [
        {
            "id": 1,
            "name": "Dr. Alice Johnson",
            "email": "alice@example.com",
            "license_no": "TH-001",
            "specialization": "CBT",
            "status": "active"
        },
        {
            "id": 2,
            "name": "Dr. Bob Smith",
            "email": "bob@example.com",
            "license_no": "TH-002",
            "specialization": "Family Therapy",
            "status": "active"
        },
        {
            "id": 3,
            "name": "Dr. Carol Davis",
            "email": "carol@example.com",
            "license_no": "TH-003",
            "specialization": "Trauma Therapy",
            "status": "inactive"
        }
    ]


@pytest.fixture
def mock_admin_user() -> dict:
    """
    Provide mock admin user data from token.
    
    Returns:
        Dictionary with admin user information
    """
    return {
        "username": "admin_user",
        "role": "admin",
        "user_id": 1,
        "email": "admin@example.com"
    }


@pytest.fixture
def mock_regular_user() -> dict:
    """
    Provide mock regular user data from token.
    
    Returns:
        Dictionary with regular user information
    """
    return {
        "username": "regular_user",
        "role": "clinician",
        "user_id": 2,
        "email": "user@example.com"
    }


@pytest.fixture
def mock_therapist_service() -> AsyncMock:
    """
    Create a mock TherapistService for testing routes.
    
    Returns:
        AsyncMock of TherapistService
    """
    service = AsyncMock()
    
    # Configure mock methods
    service.get_all_therapists = AsyncMock(return_value=[
        {
            "id": 1,
            "name": "Dr. Test",
            "email": "test@example.com",
            "license_no": "TH-001",
            "specialization": "Test",
            "status": "active"
        }
    ])
    
    service.get_therapist_by_id = AsyncMock(return_value={
        "id": 1,
        "name": "Dr. Test",
        "email": "test@example.com",
        "license_no": "TH-001",
        "specialization": "Test",
        "status": "active"
    })
    
    service.create_therapist = AsyncMock(return_value={
        "id": 2,
        "name": "Dr. New",
        "email": "new@example.com",
        "license_no": "TH-002",
        "specialization": "New",
        "status": "active"
    })
    
    service.update_therapist = AsyncMock(return_value={
        "id": 1,
        "name": "Dr. Updated",
        "email": "updated@example.com",
        "license_no": "TH-001",
        "specialization": "Updated",
        "status": "active"
    })
    
    service.delete_therapist = AsyncMock(return_value=True)
    
    service.get_therapist_sessions = AsyncMock(return_value=[
        {
            "id": 1,
            "therapist_id": 1,
            "patient_id": 101,
            "date": "2024-01-15T10:00:00",
            "duration": 60,
            "notes": "Test session",
            "status": "completed"
        }
    ])
    
    return service


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


# Test session scope helpers
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Utility functions for testing

def create_auth_headers(token: str) -> dict:
    """
    Create Authorization header for API requests.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary with Authorization header
    """
    return {"Authorization": f"Bearer {token}"}


def get_response_json(response) -> dict:
    """
    Extract JSON from response safely.
    
    Args:
        response: FastAPI test response
        
    Returns:
        Parsed JSON or empty dict if invalid
    """
    try:
        return response.json()
    except Exception:
        return {}


# Assertion helpers

def assert_therapist_fields(therapist: dict):
    """
    Assert that therapist object has all required fields.
    
    Args:
        therapist: Therapist dictionary
        
    Raises:
        AssertionError: If required fields are missing
    """
    required_fields = [
        "id", "name", "email", "license_no", 
        "specialization", "status", "created_at"
    ]
    for field in required_fields:
        assert field in therapist, f"Missing required field: {field}"


def assert_error_response(response, expected_status: int, expected_detail: str = None):
    """
    Assert error response has correct format.
    
    Args:
        response: API response
        expected_status: Expected HTTP status code
        expected_detail: Expected error detail message (optional)
        
    Raises:
        AssertionError: If assertions fail
    """
    assert response.status_code == expected_status
    data = response.json()
    assert "detail" in data, "Error response missing 'detail' field"
    if expected_detail:
        assert expected_detail in data["detail"]
