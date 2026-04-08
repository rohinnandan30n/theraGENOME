"""
FAERS Parser for Dev3 - Drug Safety & Toxicity API.
Parses FDA Adverse Event Reporting System (FAERS) data with security validation.
"""

import logging
import csv
from io import StringIO
from typing import Dict, List, Any

# Security: Import file validator
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))
from shared.utils.file_validator import FileValidator, FileValidationError

logger = logging.getLogger(__name__)


class FAERSParser:
    """Parser for FAERS adverse event reports with security validation."""
    
    # FAERS Parser configuration
    ALLOWED_EXTENSIONS = [".txt", ".csv"]
    MAX_SIZE_MB = 100
    MAGIC_CHECK_TYPE = "CSV"
    
    REQUIRED_COLUMNS = ['PatientID', 'EventDate', 'EventType', 'Severity']
    
    def __init__(self):
        self.validator = FileValidator()
    
    async def parse(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Main parse function - performs security checks FIRST.
        
        Args:
            file_content: Raw file bytes from upload
            filename: Original filename from upload
            
        Returns:
            Parsed FAERS data structure
            
        Raises:
            FileValidationError: If any security check fails
        """
        # SECURITY: Validate file BEFORE any processing
        logger.info(f"Starting FAERS file validation: {filename}")
        
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
        # Proceed with normal FAERS parsing
        return self._parse_faers_content(file_content, safe_filename)
    
    def _parse_faers_content(self, file_content: bytes, safe_filename: str) -> Dict[str, Any]:
        """
        Internal FAERS parsing logic (existing parsing code).
        Only called after security validation passes.
        """
        try:
            text_content = file_content.decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode FAERS file as UTF-8: {e}")
            raise ValueError("FAERS file must be UTF-8 encoded")
        
        # Parse CSV/TSV format (detect delimiter)
        delimiter = self._detect_delimiter(text_content)
        
        try:
            csv_reader = csv.DictReader(StringIO(text_content), delimiter=delimiter)
            reports = []
            
            for i, row in enumerate(csv_reader):
                if i > 10000:  # Limit to 10k records for batch processing
                    logger.warning(f"FAERS file has >10000 records, limiting to 10000")
                    break
                
                # Validate required columns exist
                if not all(col in row for col in self.REQUIRED_COLUMNS):
                    logger.warning(f"Row {i+1} missing required columns, skipping")
                    continue
                
                reports.append({
                    "patient_id": row.get('PatientID', ''),
                    "event_date": row.get('EventDate', ''),
                    "event_type": row.get('EventType', ''),
                    "severity": row.get('Severity', ''),
                    "description": row.get('EventDescription', ''),
                    "outcome": row.get('Outcome', '')
                })
            
            return {
                "filename": safe_filename,
                "report_count": len(reports),
                "reports": reports,
                "parser_version": "1.0"
            }
        
        except Exception as e:
            logger.error(f"Failed to parse FAERS CSV: {e}")
            raise ValueError(f"Failed to parse FAERS data: {str(e)}")
    
    def _detect_delimiter(self, text: str) -> str:
        """Auto-detect CSV delimiter (comma or tab)."""
        if '\t' in text[:500]:
            return '\t'
        return ','
