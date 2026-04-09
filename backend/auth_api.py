"""
TheraGenome Authentication API
================================
Handles patient login and doctor registration with verification.
"""

from fastapi import APIRouter, HTTPException, Response, Cookie
from typing import Optional
from backend.auth import (
    PatientLoginRequest,
    DoctorRegistrationRequest,
    LoginResponse,
    UserInfoResponse,
    authenticate_user,
    create_user,
    get_user_by_email,
    generate_session_token,
)

auth_router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Session storage (in production, use Redis or database)
sessions = {}


@auth_router.post("/login", response_model=LoginResponse)
async def login(request: PatientLoginRequest, response: Response) -> LoginResponse:
    """
    Patient login endpoint
    
    Args:
        request: Contains email, password, and role
        
    Returns:
        LoginResponse with user info if successful
        
    Raises:
        HTTPException 401 if credentials are invalid
    """
    # Authenticate user
    user = authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    if user.role != "patient":
        raise HTTPException(
            status_code=403,
            detail="This login is for patients only. Doctors should use the registration endpoint."
        )
    
    # Generate session token
    session_token = generate_session_token()
    sessions[session_token] = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }
    
    # Set secure cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=86400  # 24 hours
    )
    
    return LoginResponse(
        success=True,
        message="Login successful",
        user=UserInfoResponse(
            email=user.email,
            role=user.role,
            full_name=user.full_name
        )
    )


@auth_router.post("/register-doctor", response_model=LoginResponse)
async def register_doctor(request: DoctorRegistrationRequest, response: Response) -> LoginResponse:
    """
    Doctor registration endpoint
    
    Args:
        request: Contains doctor details (email, password, license number, specialization)
        
    Returns:
        LoginResponse with user info if successful
        
    Raises:
        HTTPException 400 if data is invalid or user already exists
    """
    # Validate medical email domain
    email_domain = request.email.split('@')[1].lower()
    medical_domains = ['hospital', 'clinic', 'medical', 'health', 'healthcare', 'med', 'dr', 'doctor', '.edu', 'university']
    
    if not any(med_domain in email_domain for med_domain in medical_domains):
        raise HTTPException(
            status_code=400,
            detail="Please use an official medical institution email (hospital, clinic, medical, etc.)"
        )
    
    # Validate license number
    if len(request.license_number) < 5:
        raise HTTPException(
            status_code=400,
            detail="License number must be valid (at least 5 characters)"
        )
    
    # Validate password
    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )
    
    # Check if user already exists
    existing_user = get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    try:
        # Create doctor user
        user = create_user(
            email=request.email,
            password=request.password,
            role="doctor",
            full_name=request.full_name,
            license_number=request.license_number,
            specialization=request.specialization
        )
        
        # Generate session token
        session_token = generate_session_token()
        sessions[session_token] = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role
        }
        
        # Set secure cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400  # 24 hours
        )
        
        return LoginResponse(
            success=True,
            message="Doctor registration successful. Your account is pending verification.",
            user=UserInfoResponse(
                email=user.email,
                role=user.role,
                full_name=user.full_name,
                specialization=user.specialization,
                is_verified=user.is_verified
            )
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@auth_router.get("/user", response_model=UserInfoResponse)
async def get_current_user(session_token: Optional[str] = Cookie(None)):
    """
    Get current logged-in user info
    
    Args:
        session_token: Session cookie
        
    Returns:
        UserInfoResponse with user details
        
    Raises:
        HTTPException 401 if not authenticated
    """
    if not session_token or session_token not in sessions:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    session = sessions[session_token]
    user = get_user_by_email(session["email"])
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    
    return UserInfoResponse(
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        specialization=user.specialization,
        is_verified=user.is_verified
    )


@auth_router.post("/logout")
async def logout(response: Response):
    """
    Logout endpoint
    
    Clears session cookie
    """
    response.delete_cookie("session_token")
    return {"success": True, "message": "Logged out successfully"}


@auth_router.get("/verify-session")
async def verify_session(session_token: Optional[str] = Cookie(None)):
    """
    Verify if session is valid
    
    Args:
        session_token: Session cookie
        
    Returns:
        Dict with session status
    """
    if session_token and session_token in sessions:
        session = sessions[session_token]
        user = get_user_by_email(session["email"])
        if user:
            return {
                "authenticated": True,
                "role": user.role,
                "email": user.email
            }
    
    return {"authenticated": False}
