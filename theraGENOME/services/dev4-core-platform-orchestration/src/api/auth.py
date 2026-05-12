"""
JWT Authentication system for TheraGenome API.
Handles token generation, validation, and role-based access control.

Features:
- JWT token generation for doctor/patient roles
- Token validation with expiry checking
- Role-based access control with decorators
- Patient data isolation enforcement
- Internal service authentication with API keys
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
from functools import wraps
import uuid
import logging

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# JWT Configuration (from environment variables)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))
JWT_REFRESH_EXPIRY_DAYS = int(os.getenv("JWT_REFRESH_EXPIRY_DAYS", "7"))
INTERNAL_SERVICE_KEY = os.getenv("INTERNAL_SERVICE_KEY", "dev-internal-key-change-in-production")


# ============================================================================
# Pydantic Schemas
# ============================================================================

class LoginRequest(BaseModel):
    """User login request."""
    patient_id: str  # Can be patient ID or doctor ID
    password: str
    role: str  # "doctor" or "patient"


class TokenResponse(BaseModel):
    """Token response after successful login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # in seconds
    role: str


class CurrentUser(BaseModel):
    """Current authenticated user information."""
    id: str
    role: str  # "doctor" or "patient"


class JWTPayload(BaseModel):
    """JWT token payload."""
    sub: str  # User ID
    role: str  # User role
    jti: str  # JWT ID for revocation
    iat: datetime  # Issued at
    exp: datetime  # Expiration time


# ============================================================================
# Token Generation
# ============================================================================

def create_access_token(
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User identifier (patient_id or doctor_id)
        role: User role ("doctor" or "patient")
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=JWT_EXPIRY_MINUTES)
    
    now = datetime.utcnow()
    expire = now + expires_delta
    
    payload = {
        "sub": user_id,
        "role": role,
        "jti": str(uuid.uuid4()),
        "iat": now.isoformat(),
        "exp": expire.isoformat()
    }
    
    encoded_jwt = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )
    
    logger.info(f"Token created for user {user_id} with role {role}")
    return encoded_jwt


def create_refresh_token(user_id: str, role: str) -> str:
    """
    Create a refresh token with longer expiration.
    
    Args:
        user_id: User identifier
        role: User role
        
    Returns:
        Encoded JWT refresh token
    """
    expires_delta = timedelta(days=JWT_REFRESH_EXPIRY_DAYS)
    return create_access_token(user_id, role, expires_delta)


# ============================================================================
# Token Validation
# ============================================================================

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security)
) -> CurrentUser:
    """
    Validate JWT token and return current user.
    
    Args:
        credentials: HTTP bearer credentials
        
    Returns:
        CurrentUser with id and role
        
    Raises:
        HTTPException 401: Invalid or expired token
        HTTPException 403: Token tampered or revoked
    """
    token = credentials.credentials
    
    try:
        # Decode JWT
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        jti: str = payload.get("jti")
        
        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required claims",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate role
        if role not in ["doctor", "patient"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid role in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"Token validated for user {user_id} with role {role}")
        return CurrentUser(id=user_id, role=role)
    
    except JWTError as e:
        logger.warning(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# Role-Based Access Control
# ============================================================================

def require_role(allowed_roles: List[str]):
    """
    Decorator to enforce role-based access control.
    
    Args:
        allowed_roles: List of roles allowed to access the endpoint
        
    Returns:
        Decorated function
        
    Usage:
        @require_role(["doctor"])
        async def admin_endpoint(current_user: CurrentUser = Depends(get_current_user)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: CurrentUser = None, **kwargs):
            # If current_user is None, authentication failed earlier
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check if user's role is allowed
            if current_user.role not in allowed_roles:
                logger.warning(
                    f"Access denied for user {current_user.id} with role {current_user.role}. "
                    f"Allowed roles: {allowed_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                )
            
            # Call the original function
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# Patient Data Isolation
# ============================================================================

def verify_patient_owns_resource(
    current_user: CurrentUser,
    resource_patient_id: str
) -> None:
    """
    Verify that a patient can only access their own data.
    Doctors can access any patient's data.
    
    Args:
        current_user: Authenticated user
        resource_patient_id: Patient ID of the resource being accessed
        
    Raises:
        HTTPException 403: Patient trying to access another patient's data
    """
    # Doctors can access any patient's data
    if current_user.role == "doctor":
        return
    
    # Patients can only access their own data
    if current_user.role == "patient" and current_user.id != resource_patient_id:
        logger.warning(
            f"Patient {current_user.id} attempted to access patient {resource_patient_id}'s data"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own data"
        )


# ============================================================================
# Internal Service Authentication
# ============================================================================

def verify_internal_service_key(api_key: str) -> bool:
    """
    Verify internal service API key for inter-service communication.
    
    Args:
        api_key: API key from X-Internal-Service-Key header
        
    Returns:
        True if key is valid
        
    Raises:
        HTTPException 403: Invalid or missing API key
    """
    if not api_key or api_key != INTERNAL_SERVICE_KEY:
        logger.warning(f"Invalid internal service key attempt: {api_key[:10] if api_key else 'None'}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal service key"
        )
    return True


def get_internal_service_key() -> str:
    """Get the internal service key for making requests to other services."""
    return INTERNAL_SERVICE_KEY


# ============================================================================
# Middleware for Internal Service Key Validation
# ============================================================================

class InternalServiceKeyMiddleware:
    """Middleware to validate internal service key for inter-service requests."""
    
    def __init__(self, app, protected_paths: List[str] = None):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI application
            protected_paths: List of path prefixes to protect with internal key
                           Default: ["/internal", "/admin"]
        """
        self.app = app
        self.protected_paths = protected_paths or ["/internal", "/admin"]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        path = scope["path"]
        
        # Check if this path requires internal service key
        if any(path.startswith(p) for p in self.protected_paths):
            # Get headers
            headers = dict(scope.get("headers", []))
            api_key = headers.get(b"x-internal-service-key", b"").decode()
            
            if not api_key or api_key != INTERNAL_SERVICE_KEY:
                logger.warning(f"Unauthorized internal request to {path}")
                
                # Return 403 Forbidden
                await send({
                    "type": "http.response.start",
                    "status": 403,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"detail": "Invalid internal service key"}',
                })
                return
        
        await self.app(scope, receive, send)


# ============================================================================
# Password Hashing (for login validation)
# ============================================================================

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)
