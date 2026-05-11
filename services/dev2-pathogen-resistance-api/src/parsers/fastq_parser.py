"""
FASTQ Parser for Dev2 - Pathogen Resistance API.
Parses FASTQ files (sequencing reads) with file upload security validation.
"""

import logging
from typing import Dict, List, Any

# Security: Import file validator
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))
from shared.utils.file_validator import FileValidator, FileValidationError

logger = logging.getLogger(__name__)


class FASTQParser:
    """Parser for FASTQ files with security validation."""
    
    # FASTQ Parser configuration
    ALLOWED_EXTENSIONS = [".fastq", ".fastq.gz", ".fq", ".bam"]
    MAX_SIZE_MB = 500
    MAGIC_CHECK_TYPE = "FASTQ"
    
    def __init__(self):
        self.validator = FileValidator()
    
    async def parse(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Main parse function - performs security checks FIRST.
        
        Args:
            file_content: Raw file bytes from upload
            filename: Original filename from upload
            
        Returns:
            Parsed FASTQ data structure
            
        Raises:
            FileValidationError: If any security check fails
        """
        # SECURITY: Validate file BEFORE any processing
        logger.info(f"Starting FASTQ file validation: {filename}")
        
        try:
            # 1. Validate file extension
            self.validator.validate_extension(filename, self.ALLOWED_EXTENSIONS)
            
            # 2. Validate file size
            self.validator.validate_size(file_content, max_mb=self.MAX_SIZE_MB)
            
            # 3. Validate magic bytes
            self.validator.validate_magic_bytes(file_content, self.MAGIC_CHECK_TYPE)
            
            # 4. Sanitize filename
            safe_filename = self.validator.sanitize_filename(filename)
            logger.info(f"Sanitized filename: {filename} -> {safe_filename}")
            
            # 5. Scan for malicious content
            self.validator.scan_for_malicious_content(file_content)
            
            logger.info(f"File '{safe_filename}' passed all security checks")
            
        except FileValidationError as e:
            logger.error(f"Security validation failed for file '{filename}': {e.reason}")
            # Return error response (HTTP 400 in API layer)
            raise
        
        # Only reach here if all security checks pass
        # Proceed with normal FASTQ parsing
        return self._parse_fastq_content(file_content, safe_filename)
    
    def _parse_fastq_content(self, file_content: bytes, safe_filename: str) -> Dict[str, Any]:
        """
        Internal FASTQ parsing logic (existing parsing code).
        Only called after security validation passes.
        """
        try:
            text_content = file_content.decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode FASTQ file as UTF-8: {e}")
            raise ValueError("FASTQ file must be UTF-8 encoded")
        
        lines = text_content.strip().split('\n')
        
        # Parse FASTQ records (4 lines per record)
        reads = []
        i = 0
        while i < len(lines):
            if i + 3 >= len(lines):
                break
            
            sequence_header = lines[i]
            sequence = lines[i + 1]
            quality_header = lines[i + 2]
            quality = lines[i + 3]
            
            if sequence_header.startswith('@') and quality_header.startswith('+'):
                reads.append({
                    "header": sequence_header[1:],  # Remove '@'
                    "sequence": sequence,
                    "quality": quality,
                    "length": len(sequence)
                })
            
            i += 4
        
        return {
            "filename": safe_filename,
            "read_count": len(reads),
            "reads": reads[:1000] if len(reads) > 1000 else reads,  # Limit to 1000 for summary
            "total_bases": sum(r["length"] for r in reads),
            "sample_size": len(reads)
        }
