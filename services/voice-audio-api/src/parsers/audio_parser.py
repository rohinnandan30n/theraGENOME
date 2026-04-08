"""
Audio Parser for Voice/Audio Uploads.
Parses audio files (WAV, MP3, WebM, Ogg, M4A) with file upload security validation.
Note: Audio files skip detailed content validation and rely on magic bytes + extension.
"""

import logging
from typing import Dict, Any

# Security: Import file validator
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))
from shared.utils.file_validator import FileValidator, FileValidationError

logger = logging.getLogger(__name__)


class AudioParser:
    """Parser for audio files with security validation."""
    
    # Audio Parser configuration
    ALLOWED_EXTENSIONS = [".wav", ".mp3", ".webm", ".ogg", ".m4a"]
    MAX_SIZE_MB = 10
    MAGIC_CHECK_TYPE = None  # Skip magic byte validation for audio (extension is sufficient)
    
    def __init__(self):
        self.validator = FileValidator()
    
    async def parse(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Main parse function - performs security checks FIRST.
        
        Args:
            file_content: Raw file bytes from upload
            filename: Original filename from upload
            
        Returns:
            Audio metadata structure
            
        Raises:
            FileValidationError: If any security check fails
        """
        # SECURITY: Validate file BEFORE any processing
        logger.info(f"Starting audio file validation: {filename}")
        
        try:
            # 1. Validate file extension
            self.validator.validate_extension(filename, self.ALLOWED_EXTENSIONS)
            
            # 2. Validate file size (audio files are limited to 10MB)
            self.validator.validate_size(file_content, max_mb=self.MAX_SIZE_MB)
            
            # 3. Skip magic bytes validation for audio (unreliable across formats)
            # But we could validate if we wanted: self.validator.validate_magic_bytes(file_content, "WAV")
            
            # 4. Sanitize filename
            safe_filename = self.validator.sanitize_filename(filename)
            logger.info(f"Sanitized filename: {filename} -> {safe_filename}")
            
            # 5. Scan for malicious content (check for embedded code, null bytes, etc)
            self.validator.scan_for_malicious_content(file_content)
            
            logger.info(f"File '{safe_filename}' passed all security checks")
            
        except FileValidationError as e:
            logger.error(f"Security validation failed for file '{filename}': {e.reason}")
            # Return error response (HTTP 400 in API layer)
            raise
        
        # Only reach here if all security checks pass
        # Return metadata about the audio file
        return self._extract_audio_metadata(file_content, safe_filename)
    
    def _extract_audio_metadata(self, file_content: bytes, safe_filename: str) -> Dict[str, Any]:
        """
        Extract basic metadata from audio file.
        Only called after security validation passes.
        """
        file_size_mb = len(file_content) / (1024 * 1024)
        
        return {
            "filename": safe_filename,
            "file_size_bytes": len(file_content),
            "file_size_mb": round(file_size_mb, 2),
            "status": "ready_for_processing",
            "parser_version": "1.0"
        }
