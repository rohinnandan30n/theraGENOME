"""
SQLAlchemy database models for therapist management.

Defines ORM models for therapists, sessions, and related entities.
Provides a complete schema for therapist data persistence.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class TherapyStatusEnum(str, enum.Enum):
    """Enum for therapy status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    RETIRED = "retired"


class SessionStatusEnum(str, enum.Enum):
    """Enum for therapy session status."""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class Therapist(Base):
    """
    Database model for therapist records.
    
    Stores therapist information including name, contact, credentials, and status.
    """
    
    __tablename__ = "therapists"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Personal Information
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    
    # Credentials
    license_no = Column(String(50), nullable=False, unique=True, index=True)
    license_expiry = Column(DateTime, nullable=True)
    specialization = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    
    # Location & Practice
    office_address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    
    # Status
    status = Column(
        Enum(TherapyStatusEnum),
        default=TherapyStatusEnum.ACTIVE,
        nullable=False,
        index=True
    )
    verified = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship(
        "TherapySession",
        back_populates="therapist",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Therapist(id={self.id}, name='{self.name}', email='{self.email}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'license_no': self.license_no,
            'license_expiry': self.license_expiry.isoformat() if self.license_expiry else None,
            'specialization': self.specialization,
            'bio': self.bio,
            'office_address': self.office_address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'status': self.status.value,
            'verified': self.verified,
            'approved': self.approved,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class TherapySession(Base):
    """
    Database model for therapy session records.
    
    Stores information about individual therapy sessions between 
    therapist and patient.
    """
    
    __tablename__ = "therapy_sessions"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    therapist_id = Column(
        Integer,
        ForeignKey('therapists.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    patient_id = Column(Integer, nullable=False, index=True)
    
    # Session Details
    session_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False, default=60)
    
    # Content
    session_type = Column(String(100), nullable=True)  # individual, group, family, etc.
    notes = Column(Text, nullable=True)
    outcomes = Column(Text, nullable=True)
    
    # Status
    status = Column(
        Enum(SessionStatusEnum),
        default=SessionStatusEnum.SCHEDULED,
        nullable=False,
        index=True
    )
    
    # Billing
    fee = Column(Integer, nullable=True)  # Store as cents
    paid = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    therapist = relationship(
        "Therapist",
        back_populates="sessions"
    )
    
    def __repr__(self):
        return f"<TherapySession(id={self.id}, therapist_id={self.therapist_id}, date='{self.session_date}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'therapist_id': self.therapist_id,
            'patient_id': self.patient_id,
            'session_date': self.session_date.isoformat(),
            'duration_minutes': self.duration_minutes,
            'session_type': self.session_type,
            'notes': self.notes,
            'outcomes': self.outcomes,
            'status': self.status.value,
            'fee': self.fee,
            'paid': self.paid,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class TherapistAvailability(Base):
    """
    Database model for therapist availability slots.
    
    Stores therapist working hours and available appointment times.
    """
    
    __tablename__ = "therapist_availability"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    therapist_id = Column(
        Integer,
        ForeignKey('therapists.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Availability Details
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(5), nullable=False)  # HH:MM format
    end_time = Column(String(5), nullable=False)    # HH:MM format
    
    # Status
    is_available = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<TherapistAvailability(id={self.id}, therapist_id={self.therapist_id}, day={self.day_of_week})>"


class TherapyNote(Base):
    """
    Database model for therapy session clinical notes.
    
    Stores confidential clinical notes related to therapy sessions.
    Includes assessment, treatment plan, and progress notes.
    """
    
    __tablename__ = "therapy_notes"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    session_id = Column(
        Integer,
        ForeignKey('therapy_sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    therapist_id = Column(
        Integer,
        ForeignKey('therapists.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Note Content
    assessment = Column(Text, nullable=True)
    treatment_plan = Column(Text, nullable=True)
    progress_notes = Column(Text, nullable=True)
    goals = Column(Text, nullable=True)
    
    # Clinical Flags
    requires_follow_up = Column(Boolean, default=False)
    is_confidential = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<TherapyNote(id={self.id}, session_id={self.session_id})>"


# Pydantic models for API (in a separate file, but shown here for reference)
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class TherapistBase(BaseModel):
    """Base schema for therapist."""
    name: str
    email: EmailStr
    license_no: str
    specialization: str


class TherapistCreate(TherapistBase):
    """Schema for creating therapist."""
    phone: Optional[str] = None
    bio: Optional[str] = None
    office_address: Optional[str] = None


class TherapistUpdate(BaseModel):
    """Schema for updating therapist."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    license_no: Optional[str] = None
    specialization: Optional[str] = None
    bio: Optional[str] = None
    status: Optional[str] = None


class TherapistResponse(TherapistBase):
    """Schema for therapist response."""
    id: int
    status: str
    verified: bool
    approved: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TherapySessionBase(BaseModel):
    """Base schema for therapy session."""
    therapist_id: int
    patient_id: int
    duration_minutes: int = 60


class TherapySessionCreate(TherapySessionBase):
    """Schema for creating therapy session."""
    session_date: datetime
    session_type: Optional[str] = None
    notes: Optional[str] = None


class TherapySessionResponse(TherapySessionCreate):
    """Schema for therapy session response."""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
