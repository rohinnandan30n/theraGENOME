import os
import hashlib
from pathlib import Path
from typing import Tuple
import logging

from src.config import STORAGE_PATH

logger = logging.getLogger(__name__)


class FileStorage:
    """Handle file uploads and storage"""
    
    ALLOWED_EXTENSIONS = {'.vcf', '.fastq', '.bam'}
    
    def __init__(self):
        self.storage_path = Path(STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def validate_file_extension(self, filename: str) -> bool:
        """Validate file extension"""
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Invalid file extension: {ext}. "
                f"Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        return True

    def validate_file_integrity(self, content: bytes) -> Tuple[bool, str]:
        """Validate file integrity and return hash"""
        if not content:
            raise ValueError("File content is empty")
        
        # Calculate file hash
        file_hash = hashlib.sha256(content).hexdigest()
        return True, file_hash

    def save_file(self, filename: str, content: bytes) -> str:
        """Save file to storage and return file path"""
        # Validate extension
        self.validate_file_extension(filename)
        
        # Validate integrity
        self.validate_file_integrity(content)
        
        # Create safe filename
        safe_filename = Path(filename).name
        file_path = self.storage_path / safe_filename
        
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
            logger.info(f"File saved: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise

    def read_file(self, file_path: str) -> bytes:
        """Read file from storage"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            raise

    def cleanup_file(self, file_path: str) -> bool:
        """Clean up temporary file"""
        try:
            os.remove(file_path)
            logger.info(f"File cleaned up: {file_path}")
            return True
        except Exception as e:
            logger.warning(f"Error cleaning up file: {str(e)}")
            return False
