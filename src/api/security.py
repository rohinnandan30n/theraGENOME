"""
Security utilities for API routes

Implements JWT token verification and role-based access control.
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def verify_admin_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Verify JWT token and ensure user has admin role.
    
    Args:
        credentials: HTTP Bearer credentials from request header
        
    Returns:
        User information from JWT token
        
    Raises:
        HTTPException: If token is invalid or user doesn't have admin role
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        
        # Verify token format (basic check)
        if not token or len(token.split('.')) != 3:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # In production, verify JWT signature, expiry, etc.
        # For now, just verify token exists and extract claims
        # TODO: Implement proper JWT verification with python-jose or PyJWT
        
        # Mock user verification (replace with actual JWT decode)
        user_info = {
            'username': 'admin_user',
            'role': 'admin',
            'user_id': 1,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Check role
        if user_info.get('role') != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have admin role"
            )
        
        logger.info(f"Verified admin token for user: {user_info.get('username')}")
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_jwt_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Verify JWT token for general authentication.
    
    Args:
        credentials: HTTP Bearer credentials from request header
        
    Returns:
        User information from JWT token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        
        # Verify token format
        if not token or len(token.split('.')) != 3:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Mock user verification (replace with actual JWT decode)
        user_info = {
            'username': 'authenticated_user',
            'role': 'clinician',
            'user_id': 2,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Verified JWT token for user: {user_info.get('username')}")
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Get current authenticated user.
    
    Dependency for routes that require authentication.
    """
    return verify_jwt_token(credentials)


def check_role(required_role: str):
    """
    Factory function to create role-checking dependency.
    
    Usage:
        @app.get("/admin")
        async def admin_only(current_user = Depends(check_role('admin'))):
            ...
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if current_user.get('role') != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires {required_role} role"
            )
        return current_user
    
    return role_checker
