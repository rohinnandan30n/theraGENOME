"""
API routes for therapist management

Provides endpoints for GET, POST, PUT, DELETE operations on therapist records.
Requires admin authentication for all endpoints.
Includes input sanitization and rate limiting.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
import logging

from ..security import verify_admin_token, check_role
from ..security_utils import InputValidator, log_security_event
from ..rate_limiting import get_limiter
from .therapist_service import TherapistService, get_therapist_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/therapists", tags=["therapists"])
limiter = get_limiter()


# Pydantic models for request/response validation
class TherapistBase(BaseModel):
    """Base therapist model with common fields."""
    name: str
    email: EmailStr
    license_no: str
    specialization: str
    
    @validator('name')
    def validate_name(cls, v):
        """Validate and sanitize name field."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        if len(v) > 255:
            raise ValueError('Name exceeds maximum length of 255 characters')
        
        # Check for SQL injection and XSS
        if InputValidator.is_sql_injection_risk(v):
            raise ValueError('Name contains potential SQL injection patterns')
        if InputValidator.is_xss_risk(v):
            raise ValueError('Name contains potential XSS patterns')
        
        return InputValidator.sanitize_input(v)
    
    @validator('license_no')
    def validate_license_no(cls, v):
        """Validate and sanitize license number."""
        if not v or len(v.strip()) == 0:
            raise ValueError('License number cannot be empty')
        if len(v) > 50:
            raise ValueError('License number exceeds maximum length of 50 characters')
        
        # Check for injection
        if InputValidator.is_sql_injection_risk(v):
            raise ValueError('License number contains invalid characters')
        
        return InputValidator.sanitize_input(v)
    
    @validator('specialization')
    def validate_specialization(cls, v):
        """Validate and sanitize specialization field."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Specialization cannot be empty')
        if len(v) > 255:
            raise ValueError('Specialization exceeds maximum length')
        
        if InputValidator.is_sql_injection_risk(v):
            raise ValueError('Specialization contains invalid patterns')
        if InputValidator.is_xss_risk(v):
            raise ValueError('Specialization contains invalid HTML')
        
        return InputValidator.sanitize_input(v)


class TherapistCreate(TherapistBase):
    """Schema for creating a therapist."""
    pass


class TherapistUpdate(BaseModel):
    """Schema for updating a therapist (all fields optional)."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    license_no: Optional[str] = None
    specialization: Optional[str] = None
    status: Optional[str] = None
    
    @validator('name', pre=True, always=False)
    def validate_name_optional(cls, v):
        """Validate name if provided."""
        if v is None:
            return v
        if not isinstance(v, str) or len(v.strip()) == 0:
            raise ValueError('Name cannot be empty if provided')
        if InputValidator.is_sql_injection_risk(v) or InputValidator.is_xss_risk(v):
            raise ValueError('Name contains invalid characters')
        return InputValidator.sanitize_input(v)
    
    @validator('specialization', pre=True, always=False)
    def validate_specialization_optional(cls, v):
        """Validate specialization if provided."""
        if v is None:
            return v
        if InputValidator.is_sql_injection_risk(v) or InputValidator.is_xss_risk(v):
            raise ValueError('Specialization contains invalid characters')
        return InputValidator.sanitize_input(v)


class TherapistResponse(TherapistBase):
    """Schema for therapist response."""
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Routes

@router.get("/", response_model=List[TherapistResponse])
@limiter.limit("100/minute")
async def list_therapists(
    request: Request,
    current_user: Dict[str, Any] = Depends(verify_admin_token),
    service: TherapistService = Depends(get_therapist_service)
) -> List[Dict[str, Any]]:
    """
    Get all therapists (Admin only).
    
    Requires admin authentication via JWT token in Authorization header.
    
    Args:
        current_user: Verified admin user from token
        service: TherapistService instance
        
    Returns:
        List of all therapists
    """
    try:
        logger.info(f"Admin {current_user['username']} fetching all therapists")
        therapists = await service.get_all_therapists()
        return therapists
    except Exception as e:
        logger.error(f"Error listing therapists: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving therapists"
        )


@router.get("/{therapist_id}", response_model=TherapistResponse)
@limiter.limit("100/minute")
async def get_therapist(
    therapist_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(verify_admin_token),
    service: TherapistService = Depends(get_therapist_service)
) -> Dict[str, Any]:
    """
    Get a specific therapist by ID (Admin only).
    
    Args:
        therapist_id: The therapist's ID
        current_user: Verified admin user from token
        service: TherapistService instance
        
    Returns:
        Therapist record
        
    Raises:
        HTTPException: 404 if therapist not found
    """
    try:
        therapist = await service.get_therapist_by_id(therapist_id)
        if not therapist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Therapist {therapist_id} not found"
            )
        
        logger.info(f"Admin {current_user['username']} retrieved therapist {therapist_id}")
        return therapist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching therapist {therapist_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving therapist"
        )


@router.post("/", response_model=TherapistResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("50/minute")
async def create_therapist(
    request: Request,
    therapist: TherapistCreate,
    current_user: Dict[str, Any] = Depends(verify_admin_token),
    service: TherapistService = Depends(get_therapist_service)
) -> Dict[str, Any]:
    """
    Create a new therapist (Admin only).
    
    Args:
        therapist: Therapist data to create
        current_user: Verified admin user from token
        service: TherapistService instance
        
    Returns:
        Created therapist record
    """
    try:
        therapist_data = therapist.dict()
        new_therapist = await service.create_therapist(therapist_data)
        
        logger.info(f"Admin {current_user['username']} created therapist: {new_therapist['name']}")
        return new_therapist
    except Exception as e:
        logger.error(f"Error creating therapist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating therapist"
        )


@router.put("/{therapist_id}", response_model=TherapistResponse)
@limiter.limit("50/minute")
async def update_therapist(
    therapist_id: int,
    request: Request,
    update_data: TherapistUpdate,
    current_user: Dict[str, Any] = Depends(verify_admin_token),
    service: TherapistService = Depends(get_therapist_service)
) -> Dict[str, Any]:
    """
    Update a therapist (Admin only).
    
    Args:
        therapist_id: The therapist's ID
        update_data: Fields to update
        current_user: Verified admin user from token
        service: TherapistService instance
        
    Returns:
        Updated therapist record
        
    Raises:
        HTTPException: 404 if therapist not found
    """
    try:
        # First check if therapist exists
        therapist = await service.get_therapist_by_id(therapist_id)
        if not therapist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Therapist {therapist_id} not found"
            )
        
        # Update only provided fields
        update_fields = {k: v for k, v in update_data.dict().items() if v is not None}
        updated_therapist = await service.update_therapist(therapist_id, update_fields)
        
        logger.info(f"Admin {current_user['username']} updated therapist {therapist_id}")
        return updated_therapist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating therapist {therapist_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating therapist"
        )


@router.delete("/{therapist_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_therapist(
    therapist_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(verify_admin_token),
    service: TherapistService = Depends(get_therapist_service)
) -> None:
    """
    Delete a therapist (Admin only).
    
    Args:
        therapist_id: The therapist's ID
        current_user: Verified admin user from token
        service: TherapistService instance
        
    Raises:
        HTTPException: 404 if therapist not found
    """
    try:
        # First check if therapist exists
        therapist = await service.get_therapist_by_id(therapist_id)
        if not therapist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Therapist {therapist_id} not found"
            )
        
        await service.delete_therapist(therapist_id)
        logger.info(f"Admin {current_user['username']} deleted therapist {therapist_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting therapist {therapist_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting therapist"
        )


@router.get("/{therapist_id}/sessions", tags=["sessions"])
@limiter.limit("100/minute")
async def get_therapist_sessions(
    therapist_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(verify_admin_token),
    service: TherapistService = Depends(get_therapist_service)
) -> List[Dict[str, Any]]:
    """
    Get all therapy sessions for a specific therapist (Admin only).
    
    Args:
        therapist_id: The therapist's ID
        current_user: Verified admin user from token
        service: TherapistService instance
        
    Returns:
        List of therapy sessions
        
    Raises:
        HTTPException: 404 if therapist not found
    """
    try:
        # First check if therapist exists
        therapist = await service.get_therapist_by_id(therapist_id)
        if not therapist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Therapist {therapist_id} not found"
            )
        
        sessions = await service.get_therapist_sessions(therapist_id)
        logger.info(f"Admin {current_user['username']} retrieved sessions for therapist {therapist_id}")
        return sessions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sessions for therapist {therapist_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sessions"
        )
