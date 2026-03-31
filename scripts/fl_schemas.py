"""Pydantic schemas for Federated Learning operations.

This module defines all request/response models for the FL coordinator service,
including round management, metrics tracking, and differential privacy configuration.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class FLRoundStatus(str, Enum):
    """Status of a federated learning round."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AggregationStrategy(str, Enum):
    """Model aggregation strategy."""
    FEDAVG = "FedAvg"
    FEDMEDIAN = "FedMedian"
    FEDTRIMMEDAVG = "FedTrimmedAvg"


# ============================================================================
# Differential Privacy Configuration
# ============================================================================

class DifferentialPrivacyConfig(BaseModel):
    """Configuration for differential privacy during aggregation."""
    epsilon: float = Field(1.0, ge=0.1, le=10.0, description="Privacy budget (lower = more privacy)")
    delta: float = Field(1e-5, ge=1e-8, le=1e-3, description="Privacy failure probability")
    noise_mechanism: str = Field("gaussian", description="Noise addition mechanism")
    
    class Config:
        schema_extra = {
            "example": {
                "epsilon": 1.0,
                "delta": 1e-5,
                "noise_mechanism": "gaussian"
            }
        }


# ============================================================================
# Client Participation
# ============================================================================

class ClientUpdate(BaseModel):
    """Model update from a single hospital client."""
    hospital_id: str = Field(..., description="Unique identifier for the hospital")
    client_id: str = Field(..., description="Unique identifier for the client node")
    num_samples: int = Field(..., ge=1, description="Number of training samples used")
    local_loss: float = Field(..., description="Local model loss")
    local_accuracy: float = Field(..., ge=0.0, le=1.0, description="Local model accuracy")
    metrics: Optional[Dict[str, float]] = Field(None, description="Additional metrics (precision, recall, etc.)")
    update_timestamp: datetime = Field(default_factory=datetime.utcnow)


class ParticipatingClient(BaseModel):
    """Information about a client participating in a round."""
    hospital_id: str
    client_id: str
    num_samples: int
    local_loss: float
    local_accuracy: float
    status: str = "completed"  # completed, timeout, error


# ============================================================================
# FL Round Management
# ============================================================================

class StartFLRoundRequest(BaseModel):
    """Request to start a new federated learning round."""
    min_clients: int = Field(3, ge=1, le=100, description="Minimum clients to proceed with aggregation")
    max_clients: int = Field(50, ge=1, le=500, description="Maximum clients to accept")
    round_timeout_seconds: int = Field(300, ge=30, le=3600, description="Timeout for collecting client updates")
    privacy_config: Optional[DifferentialPrivacyConfig] = Field(None, description="Differential privacy settings")
    model_version: Optional[str] = Field(None, description="Model version identifier")
    initiated_by: Optional[str] = Field(None, description="Admin user initiating the round")
    
    class Config:
        schema_extra = {
            "example": {
                "min_clients": 3,
                "max_clients": 50,
                "round_timeout_seconds": 300,
                "privacy_config": {
                    "epsilon": 1.0,
                    "delta": 1e-5,
                    "noise_mechanism": "gaussian"
                },
                "initiated_by": "admin@hospital.org"
            }
        }


class FLRoundMetrics(BaseModel):
    """Aggregated metrics from a federated learning round."""
    round_number: int = Field(..., ge=1)
    num_clients: int = Field(..., ge=0)
    aggregated_loss: Optional[float] = Field(None, description="Global model loss")
    aggregated_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Global model accuracy")
    aggregated_metrics: Optional[Dict[str, float]] = Field(None, description="Additional aggregated metrics")
    
    class Config:
        schema_extra = {
            "example": {
                "round_number": 1,
                "num_clients": 5,
                "aggregated_loss": 0.234,
                "aggregated_accuracy": 0.923,
                "aggregated_metrics": {
                    "precision": 0.918,
                    "recall": 0.911,
                    "auc": 0.956
                }
            }
        }


class FLRoundResponse(BaseModel):
    """Response from starting/querying a federated learning round."""
    round_id: UUID
    round_number: int
    status: FLRoundStatus
    num_clients: int
    aggregated_loss: Optional[float]
    aggregated_accuracy: Optional[float]
    aggregated_metrics: Optional[Dict[str, Any]]
    
    # Privacy Settings
    privacy_epsilon: Optional[float]
    privacy_delta: Optional[float]
    noise_stddev: Optional[float]
    
    # Timing
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    
    # Participation
    participating_clients: Optional[List[str]]
    failed_clients: Optional[List[str]]
    
    # Metadata
    aggregation_strategy: str
    model_version: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "round_id": "550e8400-e29b-41d4-a716-446655440000",
                "round_number": 1,
                "status": "completed",
                "num_clients": 5,
                "aggregated_loss": 0.234,
                "aggregated_accuracy": 0.923,
                "privacy_epsilon": 1.0,
                "privacy_delta": 1e-05,
                "noise_stddev": 0.118,
                "duration_seconds": 45.2,
                "participating_clients": ["HOSP_001", "HOSP_002", "HOSP_003"],
                "aggregation_strategy": "FedAvg",
                "model_version": "v1.0",
                "created_at": "2026-03-31T10:30:00Z"
            }
        }


class StartFLRoundResponse(BaseModel):
    """Immediate response when starting an FL round."""
    round_id: UUID
    round_number: int
    status: FLRoundStatus
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "round_id": "550e8400-e29b-41d4-a716-446655440000",
                "round_number": 1,
                "status": "in_progress",
                "message": "Round 1 started. Waiting for client updates (min: 3 clients)."
            }
        }


# ============================================================================
# FL Statistics & Reporting
# ============================================================================

class FLRoundStats(BaseModel):
    """Statistics about a federated learning round."""
    round_number: int
    num_completed: int
    num_failed: int
    avg_client_loss: Optional[float]
    avg_client_accuracy: Optional[float]
    aggregated_loss: Optional[float]
    aggregated_accuracy: Optional[float]
    min_duration: Optional[float]
    max_duration: Optional[float]
    avg_duration: Optional[float]


class FLSystemStats(BaseModel):
    """Overall federated learning system statistics."""
    total_rounds_completed: int
    total_rounds_failed: int
    avg_clients_per_round: float
    avg_global_loss: float
    avg_global_accuracy: float
    privacy_epsilon_used: float
    total_privacy_budget_consumed: float


# ============================================================================
# Database Models
# ============================================================================

class FLRoundCreate(BaseModel):
    """Model for creating a new FL round in database."""
    round_number: int
    num_clients: int
    aggregation_strategy: str = "FedAvg"
    status: FLRoundStatus = FLRoundStatus.PENDING
    privacy_epsilon: Optional[float] = None
    privacy_delta: Optional[float] = None
    noise_stddev: Optional[float] = None
    participating_clients: Optional[List[str]] = None
    failed_clients: Optional[List[str]] = None
    model_version: Optional[str] = None
    initiated_by: Optional[str] = None
    created_by: Optional[str] = None


class FLRoundUpdate(BaseModel):
    """Model for updating an existing FL round."""
    status: Optional[FLRoundStatus] = None
    num_clients: Optional[int] = None
    aggregated_loss: Optional[float] = None
    aggregated_accuracy: Optional[float] = None
    aggregated_metrics: Optional[Dict[str, float]] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    noise_stddev: Optional[float] = None
    participating_clients: Optional[List[str]] = None
    failed_clients: Optional[List[str]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class FLRoundInDB(BaseModel):
    """Model for FL round as stored in database."""
    round_id: UUID
    round_number: int
    num_clients: int
    aggregated_loss: Optional[float]
    aggregated_accuracy: Optional[float]
    aggregated_metrics: Optional[Dict[str, Any]]
    status: FLRoundStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    privacy_epsilon: Optional[float]
    privacy_delta: Optional[float]
    noise_stddev: Optional[float]
    participating_clients: Optional[List[str]]
    failed_clients: Optional[List[str]]
    model_version: Optional[str]
    aggregation_strategy: str
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    initiated_by: Optional[str]
    
    class Config:
        from_attributes = True
