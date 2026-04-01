"""Repository for federated learning round metrics and management.

This module handles all database operations for FL rounds, including creating,
retrieving, updating, and deleting round records with full audit trail support.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Enum as SQLEnum, ForeignKey
import sqlalchemy as sa

from scripts.fl_schemas import (
    FLRoundCreate, FLRoundUpdate, FLRoundInDB, FLRoundStatus
)

logger = logging.getLogger(__name__)

# SQLAlchemy declarative base
Base = declarative_base()


# ============================================================================
# SQLAlchemy ORM Model
# ============================================================================

class FLRound(Base):
    """ORM model for federated learning rounds."""
    __tablename__ = "fl_rounds"

    round_id = Column(sa.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid())
    round_number = Column(Integer, nullable=False, unique=True)
    num_clients = Column(Integer, nullable=False)
    min_clients_available = Column(Integer, nullable=True)
    aggregated_loss = Column(Float, nullable=True)
    aggregated_accuracy = Column(Float, nullable=True)
    aggregated_metrics = Column(JSON, nullable=True)
    status = Column(
        SQLEnum(FLRoundStatus, name='fl_round_status'),
        nullable=False,
        default=FLRoundStatus.PENDING
    )
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Differential Privacy
    privacy_epsilon = Column(Float, nullable=True)
    privacy_delta = Column(Float, nullable=True)
    noise_stddev = Column(Float, nullable=True)
    
    # Client Participation
    participating_clients = Column(JSON, nullable=True)
    failed_clients = Column(JSON, nullable=True)
    
    # Model Details
    model_version = Column(String(50), nullable=True)
    aggregation_strategy = Column(String(50), nullable=False, default="FedAvg")
    epoch_count = Column(Integer, nullable=True, default=1)
    batch_size = Column(Integer, nullable=True)
    
    # Error Tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Audit Trail
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(255), nullable=True)
    initiated_by = Column(String(255), nullable=True)


# ============================================================================
# Repository Class
# ============================================================================

class FLRoundRepository:
    """Repository for FL round database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with async session."""
        self.session = session

    async def create_round(self, round_data: FLRoundCreate) -> FLRound:
        """Create a new FL round record.
        
        Args:
            round_data: FLRoundCreate model with round details
            
        Returns:
            Created FLRound model
        """
        try:
            # Get next round number if not specified
            if round_data.round_number == 0:
                last_round = await self.session.execute(
                    select(func.max(FLRound.round_number)).where(FLRound.deleted_at.is_(None))
                )
                next_number = (last_round.scalar() or 0) + 1
                round_data.round_number = next_number

            fl_round = FLRound(
                round_number=round_data.round_number,
                num_clients=round_data.num_clients,
                status=round_data.status,
                aggregation_strategy=round_data.aggregation_strategy,
                privacy_epsilon=round_data.privacy_epsilon,
                privacy_delta=round_data.privacy_delta,
                noise_stddev=round_data.noise_stddev,
                participating_clients=round_data.participating_clients,
                failed_clients=round_data.failed_clients,
                model_version=round_data.model_version,
                created_by=round_data.created_by,
                initiated_by=round_data.initiated_by,
            )
            
            self.session.add(fl_round)
            await self.session.commit()
            await self.session.refresh(fl_round)
            
            logger.info(f"Created FL round {fl_round.round_number} with ID {fl_round.round_id}")
            return fl_round
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating FL round: {str(e)}")
            raise

    async def get_round_by_id(self, round_id: UUID) -> Optional[FLRound]:
        """Retrieve FL round by round_id.
        
        Args:
            round_id: UUID of the round
            
        Returns:
            FLRound model or None if not found
        """
        try:
            result = await self.session.execute(
                select(FLRound).where(
                    and_(
                        FLRound.round_id == round_id,
                        FLRound.deleted_at.is_(None)
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error retrieving FL round {round_id}: {str(e)}")
            raise

    async def get_round_by_number(self, round_number: int) -> Optional[FLRound]:
        """Retrieve FL round by round number.
        
        Args:
            round_number: Sequential round number
            
        Returns:
            FLRound model or None if not found
        """
        try:
            result = await self.session.execute(
                select(FLRound).where(
                    and_(
                        FLRound.round_number == round_number,
                        FLRound.deleted_at.is_(None)
                    )
                ).order_by(desc(FLRound.created_at))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error retrieving FL round {round_number}: {str(e)}")
            raise

    async def get_latest_round(self) -> Optional[FLRound]:
        """Retrieve the most recent FL round.
        
        Returns:
            Most recent FLRound model or None if no rounds
        """
        try:
            result = await self.session.execute(
                select(FLRound)
                .where(FLRound.deleted_at.is_(None))
                .order_by(desc(FLRound.round_number))
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error retrieving latest FL round: {str(e)}")
            raise

    async def update_round(self, round_id: UUID, round_data: FLRoundUpdate) -> Optional[FLRound]:
        """Update an existing FL round.
        
        Args:
            round_id: UUID of the round to update
            round_data: FLRoundUpdate model with new values
            
        Returns:
            Updated FLRound model or None if not found
        """
        try:
            fl_round = await self.get_round_by_id(round_id)
            if not fl_round:
                logger.warning(f"FL round {round_id} not found for update")
                return None

            # Update only provided fields
            update_data = round_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if value is not None:
                    setattr(fl_round, field, value)

            # Update the updated_at timestamp
            fl_round.updated_at = datetime.utcnow()

            self.session.add(fl_round)
            await self.session.commit()
            await self.session.refresh(fl_round)
            
            logger.info(f"Updated FL round {round_id}")
            return fl_round
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating FL round {round_id}: {str(e)}")
            raise

    async def get_all_rounds(self, limit: int = 100, offset: int = 0) -> List[FLRound]:
        """Retrieve all FL rounds with pagination.
        
        Args:
            limit: Maximum number of rounds to retrieve
            offset: Number of rounds to skip
            
        Returns:
            List of FLRound models
        """
        try:
            result = await self.session.execute(
                select(FLRound)
                .where(FLRound.deleted_at.is_(None))
                .order_by(desc(FLRound.round_number))
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving all FL rounds: {str(e)}")
            raise

    async def get_rounds_by_status(self, status: FLRoundStatus) -> List[FLRound]:
        """Retrieve all FL rounds with a specific status.
        
        Args:
            status: FLRoundStatus enum value
            
        Returns:
            List of FLRound models with matching status
        """
        try:
            result = await self.session.execute(
                select(FLRound)
                .where(
                    and_(
                        FLRound.status == status,
                        FLRound.deleted_at.is_(None)
                    )
                )
                .order_by(desc(FLRound.round_number))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving FL rounds by status {status}: {str(e)}")
            raise

    async def get_completed_rounds(self, limit: int = 10) -> List[FLRound]:
        """Retrieve recently completed FL rounds.
        
        Args:
            limit: Maximum number of rounds to retrieve
            
        Returns:
            List of completed FLRound models
        """
        return await self.get_rounds_by_status(FLRoundStatus.COMPLETED)[:limit]

    async def soft_delete_round(self, round_id: UUID) -> bool:
        """Soft delete an FL round (set deleted_at timestamp).
        
        Args:
            round_id: UUID of the round to delete
            
        Returns:
            True if successful, False if round not found
        """
        try:
            fl_round = await self.get_round_by_id(round_id)
            if not fl_round:
                logger.warning(f"FL round {round_id} not found for deletion")
                return False

            fl_round.deleted_at = datetime.utcnow()
            self.session.add(fl_round)
            await self.session.commit()
            
            logger.info(f"Soft deleted FL round {round_id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error soft deleting FL round {round_id}: {str(e)}")
            raise

    # ========================================================================
    # Statistics and Analytics
    # ========================================================================

    async def get_round_statistics(self, round_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a specific round.
        
        Args:
            round_id: UUID of the round
            
        Returns:
            Dictionary with round statistics or None if not found
        """
        try:
            fl_round = await self.get_round_by_id(round_id)
            if not fl_round:
                return None

            stats = {
                'round_id': fl_round.round_id,
                'round_number': fl_round.round_number,
                'status': fl_round.status.value,
                'num_clients': fl_round.num_clients,
                'participating_clients': fl_round.participating_clients or [],
                'failed_clients': fl_round.failed_clients or [],
                'aggregated_loss': fl_round.aggregated_loss,
                'aggregated_accuracy': fl_round.aggregated_accuracy,
                'duration_seconds': fl_round.duration_seconds,
                'privacy_epsilon': fl_round.privacy_epsilon,
                'privacy_delta': fl_round.privacy_delta,
                'noise_stddev': fl_round.noise_stddev,
                'aggregated_metrics': fl_round.aggregated_metrics,
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting round statistics for {round_id}: {str(e)}")
            raise

    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get overall federated learning system statistics.
        
        Returns:
            Dictionary with system-wide statistics
        """
        try:
            # Count rounds by status
            all_rounds = await self.session.execute(
                select(FLRound).where(FLRound.deleted_at.is_(None))
            )
            rounds = all_rounds.scalars().all()

            completed = [r for r in rounds if r.status == FLRoundStatus.COMPLETED]
            failed = [r for r in rounds if r.status == FLRoundStatus.FAILED]

            # Calculate averages
            avg_clients = sum(r.num_clients for r in completed) / len(completed) if completed else 0
            avg_loss = sum(r.aggregated_loss for r in completed if r.aggregated_loss) / len([r for r in completed if r.aggregated_loss]) if completed else 0
            avg_accuracy = sum(r.aggregated_accuracy for r in completed if r.aggregated_accuracy) / len([r for r in completed if r.aggregated_accuracy]) if completed else 0
            
            # Privacy budget
            total_epsilon = sum(r.privacy_epsilon or 0 for r in completed)

            return {
                'total_rounds': len(rounds),
                'completed_rounds': len(completed),
                'failed_rounds': len(failed),
                'pending_rounds': len([r for r in rounds if r.status == FLRoundStatus.PENDING]),
                'in_progress_rounds': len([r for r in rounds if r.status == FLRoundStatus.IN_PROGRESS]),
                'avg_clients_per_round': avg_clients,
                'avg_global_loss': avg_loss,
                'avg_global_accuracy': avg_accuracy,
                'total_privacy_epsilon_used': total_epsilon,
            }
        except Exception as e:
            logger.error(f"Error calculating system statistics: {str(e)}")
            raise

    async def get_rounds_since(self, hours: int = 24) -> List[FLRound]:
        """Get all FL rounds from the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of FLRound models
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            result = await self.session.execute(
                select(FLRound)
                .where(
                    and_(
                        FLRound.created_at >= cutoff_time,
                        FLRound.deleted_at.is_(None)
                    )
                )
                .order_by(desc(FLRound.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving rounds from last {hours} hours: {str(e)}")
            raise

    async def get_client_participation_history(self, hospital_id: str) -> List[Dict[str, Any]]:
        """Get participation history for a specific hospital.
        
        Args:
            hospital_id: Hospital identifier
            
        Returns:
            List of round data where hospital participated
        """
        try:
            result = await self.session.execute(
                select(FLRound)
                .where(FLRound.deleted_at.is_(None))
                .order_by(desc(FLRound.round_number))
            )
            all_rounds = result.scalars().all()
            
            history = []
            for round_obj in all_rounds:
                if round_obj.participating_clients and hospital_id in round_obj.participating_clients:
                    history.append({
                        'round_number': round_obj.round_number,
                        'status': round_obj.status.value,
                        'created_at': round_obj.created_at,
                        'aggregated_loss': round_obj.aggregated_loss,
                        'aggregated_accuracy': round_obj.aggregated_accuracy,
                    })
            
            return history
        except Exception as e:
            logger.error(f"Error retrieving participation history for {hospital_id}: {str(e)}")
            raise
