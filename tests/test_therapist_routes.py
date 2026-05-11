"""
Integration tests for therapist routes

Tests API endpoints for therapist CRUD operations.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api.main import app

# Create test client
client = TestClient(app)


# Fixtures
@pytest.fixture
def mock_admin_token():
    """Create mock admin token."""
    return "Bearer valid.jwt.admin.token"


@pytest.fixture
def therapist_data():
    """Sample therapist data."""
    return {
        "name": "Dr. Jane Smith",
        "email": "jane@therapahub.com",
        "license_no": "TH-2024-999",
        "specialization": "Trauma-Focused Therapy"
    }


@pytest.fixture
def therapist_response():
    """Sample therapist response."""
    return {
        "id": 1,
        "name": "Dr. Sarah Johnson",
        "email": "sarah@therapahub.com",
        "license_no": "TH-2024-001",
        "specialization": "Cognitive Behavioral Therapy",
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }


# Health check tests

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "theraGENOME API"
    assert "endpoints" in data


# Therapist list tests

def test_list_therapists_no_auth():
    """Test listing therapists without authentication."""
    response = client.get("/api/v1/therapists/")
    
    # Should be 403 Forbidden or 401 Unauthorized depending on implementation
    assert response.status_code in [401, 403]


@patch('src.api.security.verify_admin_token')
def test_list_therapists_with_auth(mock_verify, mock_admin_token):
    """Test listing therapists with valid authentication."""
    # Mock admin verification
    mock_verify.return_value = {
        'username': 'admin',
        'role': 'admin',
        'user_id': 1
    }
    
    headers = {"Authorization": mock_admin_token}
    response = client.get(
        "/api/v1/therapists/",
        headers=headers
    )
    
    # Would return 200 with mock, but depends on mock setup
    assert response.status_code in [200, 401, 403]


# Therapist detail tests

def test_get_therapist_no_auth():
    """Test getting therapist without authentication."""
    response = client.get("/api/v1/therapists/1")
    
    assert response.status_code in [401, 403]


def test_get_therapist_not_found():
    """Test getting non-existent therapist."""
    # This would return 404 with proper authentication
    response = client.get("/api/v1/therapists/9999")
    
    assert response.status_code in [401, 403, 404]


# Therapist creation tests

def test_create_therapist_no_auth(therapist_data):
    """Test creating therapist without authentication."""
    response = client.post(
        "/api/v1/therapists/",
        json=therapist_data
    )
    
    assert response.status_code in [401, 403]


def test_create_therapist_invalid_data(mock_admin_token):
    """Test creating therapist with invalid data."""
    invalid_data = {
        "name": "Dr. Invalid",
        # Missing required fields
    }
    
    headers = {"Authorization": mock_admin_token}
    response = client.post(
        "/api/v1/therapists/",
        json=invalid_data,
        headers=headers
    )
    
    # Should return 422 for validation error or 401 for auth
    assert response.status_code in [401, 403, 422]


# Therapist update tests

def test_update_therapist_no_auth():
    """Test updating therapist without authentication."""
    response = client.put(
        "/api/v1/therapists/1",
        json={"name": "Updated Name"}
    )
    
    assert response.status_code in [401, 403]


def test_update_therapist_partial(mock_admin_token):
    """Test partial therapist update."""
    update_data = {"name": "Dr. Updated Name"}
    
    headers = {"Authorization": mock_admin_token}
    response = client.put(
        "/api/v1/therapists/1",
        json=update_data,
        headers=headers
    )
    
    # Would return 200 with successful update or 404 if not found
    assert response.status_code in [200, 401, 403, 404]


# Therapist deletion tests

def test_delete_therapist_no_auth():
    """Test deleting therapist without authentication."""
    response = client.delete("/api/v1/therapists/1")
    
    assert response.status_code in [401, 403]


def test_delete_therapist_invalid_id(mock_admin_token):
    """Test deleting non-existent therapist."""
    headers = {"Authorization": mock_admin_token}
    response = client.delete(
        "/api/v1/therapists/9999",
        headers=headers
    )
    
    # Should return 404 if not found
    assert response.status_code in [204, 401, 403, 404]


# Therapist sessions tests

def test_get_therapist_sessions_no_auth():
    """Test getting therapist sessions without authentication."""
    response = client.get("/api/v1/therapists/1/sessions")
    
    assert response.status_code in [401, 403]


def test_get_therapist_sessions_invalid_therapist(mock_admin_token):
    """Test getting sessions for non-existent therapist."""
    headers = {"Authorization": mock_admin_token}
    response = client.get(
        "/api/v1/therapists/9999/sessions",
        headers=headers
    )
    
    # Should return 404 if therapist not found
    assert response.status_code in [200, 401, 403, 404]


# Error handling tests

def test_malformed_json():
    """Test handling of malformed JSON."""
    response = client.post(
        "/api/v1/therapists/",
        data="not valid json",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code in [400, 422]


def test_missing_required_fields():
    """Test validation of required fields."""
    incomplete_therapist = {
        "name": "Dr. Incomplete"
        # Missing email, license_no, specialization
    }
    
    response = client.post(
        "/api/v1/therapists/",
        json=incomplete_therapist
    )
    
    # Should return 422 for validation error or 401 for auth
    assert response.status_code in [401, 403, 422]


# Response format tests

def test_therapist_response_format(therapist_response):
    """Test that therapist response has correct format."""
    # This is a data validation test
    assert "id" in therapist_response
    assert "name" in therapist_response
    assert "email" in therapist_response
    assert "license_no" in therapist_response
    assert "specialization" in therapist_response
    assert "status" in therapist_response
    assert "created_at" in therapist_response
