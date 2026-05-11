"""
Unit tests for security module

Tests JWT token verification and role-based access control.
"""

import pytest
from fastapi import HTTPException, status
from unittest.mock import Mock, patch, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api.security import verify_admin_token, verify_jwt_token, check_role


# Simple mock class for HTTPAuthCredentials
class HTTPAuthCredentials:
    """Mock HTTPAuthCredentials for testing."""
    def __init__(self, scheme: str, credentials: str):
        self.scheme = scheme
        self.credentials = credentials


# Fixtures
@pytest.fixture
def valid_credentials():
    """Create valid HTTP credentials."""
    return HTTPAuthCredentials(scheme="bearer", credentials="valid.jwt.token")


@pytest.fixture
def invalid_credentials():
    """Create invalid HTTP credentials."""
    return HTTPAuthCredentials(scheme="bearer", credentials="invalid")


@pytest.fixture
def no_credentials():
    """Return None for missing credentials."""
    return None


# Tests for verify_admin_token

@pytest.mark.asyncio
async def test_verify_admin_token_valid(valid_credentials):
    """Test successful admin token verification."""
    result = await verify_admin_token(valid_credentials)
    
    assert result is not None
    assert result['role'] == 'admin'
    assert 'username' in result
    assert 'user_id' in result


@pytest.mark.asyncio
async def test_verify_admin_token_no_credentials(no_credentials):
    """Test admin token verification with missing credentials."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_admin_token(no_credentials)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_verify_admin_token_invalid_format(invalid_credentials):
    """Test admin token verification with invalid token format."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_admin_token(invalid_credentials)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# Tests for verify_jwt_token

@pytest.mark.asyncio
async def test_verify_jwt_token_valid(valid_credentials):
    """Test successful JWT token verification."""
    result = await verify_jwt_token(valid_credentials)
    
    assert result is not None
    assert 'username' in result
    assert 'user_id' in result
    assert 'role' in result


@pytest.mark.asyncio
async def test_verify_jwt_token_no_credentials(no_credentials):
    """Test JWT token verification with missing credentials."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_jwt_token(no_credentials)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_verify_jwt_token_invalid_format():
    """Test JWT token verification with invalid format."""
    invalid_token = HTTPAuthCredentials(scheme="bearer", credentials="onlyonepart")
    
    with pytest.raises(HTTPException) as exc_info:
        await verify_jwt_token(invalid_token)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# Tests for check_role

@pytest.mark.asyncio
async def test_check_role_valid_role(valid_credentials):
    """Test role checking with valid admin role."""
    check_admin = check_role('admin')
    
    # Mock get_current_user to return admin user
    admin_user = {
        'username': 'admin',
        'role': 'admin',
        'user_id': 1
    }
    
    result = await check_admin(admin_user)
    assert result['role'] == 'admin'


@pytest.mark.asyncio
async def test_check_role_invalid_role(valid_credentials):
    """Test role checking with invalid role."""
    check_admin = check_role('admin')
    
    # Non-admin user
    user = {
        'username': 'clinician',
        'role': 'clinician',
        'user_id': 2
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await check_admin(user)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# Integration tests

@pytest.mark.asyncio
async def test_security_flow_complete():
    """Test complete security flow with valid token and admin role."""
    # Valid token format (3 parts separated by dots)
    valid_token = HTTPAuthCredentials(scheme="bearer", credentials="header.payload.signature")
    
    # Verify token
    user = await verify_admin_token(valid_token)
    
    # Check that user has admin role
    assert user['role'] == 'admin'
    assert 'username' in user
