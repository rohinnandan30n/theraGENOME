"""
Service layer for therapist operations.

Provides business logic for CRUD operations on therapist records.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TherapistService:
    """Service for managing therapist data."""
    
    # In-memory storage for demo (replace with actual database)
    therapists: Dict[int, Dict[str, Any]] = {}
    next_id = 1
    
    async def get_all_therapists(self) -> List[Dict[str, Any]]:
        """Get all therapists."""
        return list(self.therapists.values())
    
    async def get_therapist_by_id(self, therapist_id: int) -> Optional[Dict[str, Any]]:
        """Get a therapist by ID."""
        return self.therapists.get(therapist_id)
    
    async def create_therapist(self, therapist_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new therapist."""
        therapist_id = self.next_id
        self.next_id += 1
        
        therapist = {
            "id": therapist_id,
            **therapist_data,
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.therapists[therapist_id] = therapist
        logger.info(f"Created therapist {therapist_id}: {therapist_data.get('name')}")
        return therapist
    
    async def update_therapist(
        self,
        therapist_id: int,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a therapist."""
        if therapist_id not in self.therapists:
            return None
        
        therapist = self.therapists[therapist_id]
        therapist.update(update_data)
        
        logger.info(f"Updated therapist {therapist_id}")
        return therapist
    
    async def delete_therapist(self, therapist_id: int) -> bool:
        """Delete a therapist."""
        if therapist_id in self.therapists:
            del self.therapists[therapist_id]
            logger.info(f"Deleted therapist {therapist_id}")
            return True
        return False
    
    async def get_therapist_sessions(
        self,
        therapist_id: int
    ) -> List[Dict[str, Any]]:
        """Get all sessions for a therapist."""
        # Placeholder - would query sessions from database
        return []


# Global service instance
_therapist_service: Optional[TherapistService] = None


def get_therapist_service() -> TherapistService:
    """Dependency injection for TherapistService."""
    global _therapist_service
    if _therapist_service is None:
        _therapist_service = TherapistService()
    return _therapist_service
