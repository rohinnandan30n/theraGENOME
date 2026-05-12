from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, String, DateTime, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import hashlib
import secrets

# Database setup
DATABASE_URL = "sqlite:///./theragenome.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ===== DATABASE MODELS =====
class User(Base):
    """User model for both patients and doctors"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)  # 'patient' or 'doctor'
    full_name = Column(String, nullable=True)
    license_number = Column(String, nullable=True)  # For doctors
    specialization = Column(String, nullable=True)  # For doctors
    is_verified = Column(Boolean, default=False)  # For doctor verification
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

# ===== PYDANTIC SCHEMAS =====
class PatientLoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "patient"

class DoctorRegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    license_number: str
    specialization: str
    role: str = "doctor"

class UserInfoResponse(BaseModel):
    email: str
    role: str
    full_name: Optional[str] = None
    specialization: Optional[str] = None
    is_verified: Optional[bool] = None

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: UserInfoResponse

# ===== AUTHENTICATION UTILITIES =====
def hash_password(password: str) -> tuple[str, str]:
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return salt, password_hash.hex()

def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return password_hash.hex() == stored_hash

def generate_session_token():
    """Generate secure session token"""
    return secrets.token_urlsafe(32)

# ===== AUTHENTICATION FUNCTIONS =====
def create_user(email: str, password: str, role: str, full_name: str = None, 
                license_number: str = None, specialization: str = None) -> User:
    """Create a new user"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("User already registered with this email")

        # Hash password
        salt, password_hash = hash_password(password)
        full_hash = f"{salt}${password_hash}"

        # Create user
        user = User(
            id=secrets.token_hex(16),
            email=email,
            password_hash=full_hash,
            role=role,
            full_name=full_name,
            license_number=license_number,
            specialization=specialization,
            is_verified=(role == "patient")  # Patients are auto-verified, doctors need manual verification
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        # Extract salt and hash
        parts = user.password_hash.split('$')
        if len(parts) != 2:
            return None
        
        salt, stored_hash = parts
        
        # Verify password
        if not verify_password(password, salt, stored_hash):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Make sure attributes are loaded before detaching from session
        # Access all attributes to eagerly load them
        _ = user.id
        _ = user.email
        _ = user.role
        _ = user.full_name
        _ = user.last_login
        
        # Detach from session
        db.expunge(user)
        
        return user
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    finally:
        db.close()

def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        return user
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)
