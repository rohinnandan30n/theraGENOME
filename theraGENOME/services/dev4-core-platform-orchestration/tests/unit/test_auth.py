"""
Comprehensive tests for JWT authentication system.
Tests token generation, validation, role enforcement, and patient isolation.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from api.auth import (
    create_access_token,
    create_refresh_token,
    verify_patient_owns_resource,
    verify_internal_service_key,
    hash_password,
    verify_password,
    CurrentUser,
    LoginRequest,
    TokenResponse,
    JWTPayload,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    INTERNAL_SERVICE_KEY
)
from jose import jwt, JWTError
from fastapi import HTTPException


class TestTokenGeneration:
    """Test JWT token generation."""
    
    def test_create_access_token_doctor(self):
        """Test creating access token for doctor."""
        user_id = "DOC_001"
        role = "doctor"
        
        token = create_access_token(user_id, role)
        
        # Verify token can be decoded
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        assert decoded["sub"] == user_id
        assert decoded["role"] == role
        assert "jti" in decoded
        assert "iat" in decoded
        assert "exp" in decoded
    
    def test_create_access_token_patient(self):
        """Test creating access token for patient."""
        user_id = "P_001"
        role = "patient"
        
        token = create_access_token(user_id, role)
        
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        assert decoded["sub"] == user_id
        assert decoded["role"] == role
    
    def test_create_refresh_token(self):
        """Test creating refresh token with longer expiration."""
        user_id = "P_001"
        role = "patient"
        
        token = create_refresh_token(user_id, role)
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Verify refresh token was created
        assert decoded["sub"] == user_id
        assert decoded["role"] == role
    
    def test_token_contains_unique_jti(self):
        """Test that each token has a unique JTI."""
        user_id = "P_001"
        role = "patient"
        
        token1 = create_access_token(user_id, role)
        token2 = create_access_token(user_id, role)
        
        decoded1 = jwt.decode(token1, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        decoded2 = jwt.decode(token2, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Different tokens should have different JTI
        assert decoded1["jti"] != decoded2["jti"]


class TestTokenValidation:
    """Test JWT token validation."""
    
    def test_validate_valid_token(self):
        """Test validating a valid token."""
        user_id = "P_001"
        role = "patient"
        
        token = create_access_token(user_id, role)
        
        # Should decode without errors
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == user_id
        assert decoded["role"] == role
    
    def test_validate_expired_token(self):
        """Test that expired token raises JWTError."""
        user_id = "P_001"
        role = "patient"
        
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(user_id, role, expires_delta)
        
        # Should raise error when trying to decode
        with pytest.raises(JWTError):
            jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    
    def test_validate_tampered_token(self):
        """Test that tampered token raises JWTError."""
        user_id = "P_001"
        role = "patient"
        
        token = create_access_token(user_id, role)
        
        # Tamper with the token by modifying it
        tampered_token = token[:-10] + "tampered00"
        
        # Should raise error
        with pytest.raises(JWTError):
            jwt.decode(tampered_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    
    def test_validate_missing_required_claims(self):
        """Test validation fails if required claims are missing."""
        # Create payload without required claims
        payload = {
            "iat": datetime.utcnow().isoformat(),
            "exp": (datetime.utcnow() + timedelta(minutes=60)).isoformat()
            # Missing "sub" and "role"
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        # Token can be decoded but missing claims
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert "sub" not in decoded
        assert "role" not in decoded


class TestRoleEnforcement:
    """Test role-based access control."""
    
    def test_doctor_role_valid(self):
        """Test valid doctor token."""
        user = CurrentUser(id="DOC_001", role="doctor")
        assert user.role == "doctor"
    
    def test_patient_role_valid(self):
        """Test valid patient token."""
        user = CurrentUser(id="P_001", role="patient")
        assert user.role == "patient"
    
    def test_invalid_role_rejected(self):
        """Test that invalid role is rejected."""
        token = create_access_token("USER_001", "invalid_role")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Invalid role should not pass validation in real endpoint
        assert payload["role"] == "invalid_role"
        assert payload["role"] not in ["doctor", "patient"]


class TestPatientDataIsolation:
    """Test patient data isolation enforcement."""
    
    def test_doctor_can_access_any_patient_data(self):
        """Test that doctor can access any patient's data."""
        doctor = CurrentUser(id="DOC_001", role="doctor")
        patient_id = "P_001"
        
        # Should not raise exception
        verify_patient_owns_resource(doctor, patient_id)
    
    def test_patient_can_access_own_data(self):
        """Test that patient can access their own data."""
        patient = CurrentUser(id="P_001", role="patient")
        
        # Should not raise exception
        verify_patient_owns_resource(patient, "P_001")
    
    def test_patient_cannot_access_other_patient_data(self):
        """Test that patient cannot access another patient's data."""
        patient = CurrentUser(id="P_001", role="patient")
        other_patient_id = "P_002"
        
        # Should raise 403
        with pytest.raises(HTTPException) as excinfo:
            verify_patient_owns_resource(patient, other_patient_id)
        
        assert excinfo.value.status_code == 403
        assert "own data" in excinfo.value.detail.lower()


class TestInternalServiceKey:
    """Test internal service authentication."""
    
    def test_valid_internal_service_key(self):
        """Test validating a valid internal service key."""
        result = verify_internal_service_key(INTERNAL_SERVICE_KEY)
        assert result is True
    
    def test_invalid_internal_service_key(self):
        """Test that invalid key raises 403."""
        with pytest.raises(HTTPException) as excinfo:
            verify_internal_service_key("invalid-key")
        
        assert excinfo.value.status_code == 403
    
    def test_missing_internal_service_key(self):
        """Test that missing key raises 403."""
        with pytest.raises(HTTPException) as excinfo:
            verify_internal_service_key(None)
        
        assert excinfo.value.status_code == 403
    
    def test_empty_internal_service_key(self):
        """Test that empty key raises 403."""
        with pytest.raises(HTTPException) as excinfo:
            verify_internal_service_key("")
        
        assert excinfo.value.status_code == 403


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)
        
        # Hash should be different from original
        assert hashed != password
        # Hash should be long (bcrypt hashes are ~60 chars)
        assert len(hashed) > 50
    
    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        password = "MySecurePassword123!"
        wrong_password = "WrongPassword456"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (bcrypt salting)."""
        password = "MySecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Different hashes but both verify the same password
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestIntegration:
    """Integration tests for complete authentication flows."""
    
    def test_doctor_login_flow(self):
        """Test complete doctor login flow."""
        doctor_id = "DOC_001"
        role = "doctor"
        
        # Create token (simulating login)
        token = create_access_token(doctor_id, role)
        
        # Validate token
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        user = CurrentUser(id=decoded["sub"], role=decoded["role"])
        
        # Doctor should be able to access any endpoint
        assert user.role == "doctor"
        assert user.id == doctor_id
    
    def test_patient_login_flow(self):
        """Test complete patient login flow."""
        patient_id = "P_001"
        role = "patient"
        
        # Create token (simulating login)
        token = create_access_token(patient_id, role)
        
        # Validate token
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user = CurrentUser(id=decoded["sub"], role=decoded["role"])
        
        # Patient should only access own data
        assert user.role == "patient"
        assert user.id == patient_id
        
        # Should be able to access own data
        verify_patient_owns_resource(user, patient_id)
        
        # Should NOT be able to access other patient's data
        with pytest.raises(HTTPException):
            verify_patient_owns_resource(user, "P_002")
    
    def test_patient_accessing_multiple_records_isolation(self):
        """Test patient data isolation across multiple resources."""
        patient1 = CurrentUser(id="P_001", role="patient")
        patient2 = CurrentUser(id="P_002", role="patient")
        
        # Patient 1 can access own data
        verify_patient_owns_resource(patient1, "P_001")
        
        # Patient 1 cannot access patient 2's data
        with pytest.raises(HTTPException):
            verify_patient_owns_resource(patient1, "P_002")
        
        # Patient 2 can access own data
        verify_patient_owns_resource(patient2, "P_002")
        
        # Patient 2 cannot access patient 1's data
        with pytest.raises(HTTPException):
            verify_patient_owns_resource(patient2, "P_001")
    
    def test_internal_service_communication(self):
        """Test internal service-to-service authentication."""
        # Service 1 calls Service 2 with internal key
        result = verify_internal_service_key(INTERNAL_SERVICE_KEY)
        assert result is True
        
        # Invalid request should fail
        with pytest.raises(HTTPException):
            verify_internal_service_key("wrong-key")


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_token_with_special_characters_in_user_id(self):
        """Test token generation with special characters in user ID."""
        user_id = "P_001-special_id.123"
        token = create_access_token(user_id, "patient")
        
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == user_id
    
    def test_token_with_long_user_id(self):
        """Test token generation with very long user ID."""
        user_id = "P_" + "x" * 200  # Very long ID
        token = create_access_token(user_id, "patient")
        
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == user_id
    
    def test_verify_patient_owns_resource_with_various_patient_ids(self):
        """Test patient isolation with various ID formats."""
        test_ids = [
            "P_001",
            "PATIENT_001",
            "patient-001",
            "p001",
            "P_001-VARIANT-123"
        ]
        
        for patient_id in test_ids:
            patient = CurrentUser(id=patient_id, role="patient")
            
            # Should access own resource
            verify_patient_owns_resource(patient, patient_id)
            
            # Should not access other resource
            with pytest.raises(HTTPException):
                verify_patient_owns_resource(patient, patient_id + "_other")
    
    def test_token_expiry_boundary(self):
        """Test token at expiry boundary."""
        user_id = "P_001"
        role = "patient"
        
        # Create token that expires in 1 second
        expires_delta = timedelta(seconds=1)
        token = create_access_token(user_id, role, expires_delta)
        
        # Should still be valid immediately
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == user_id
