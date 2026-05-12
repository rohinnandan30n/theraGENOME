"""
Omics Parser for Dev4 - Core Platform Orchestration.
Parses omics data files (CSV, TSV, TXT) with security validation.
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


class OmicsParser:
    """Parser for omics data files (gene expression, proteomics, etc.) with security validation."""
    
    # Omics Parser configuration
    ALLOWED_EXTENSIONS = [".csv", ".tsv", ".txt"]
    MAX_SIZE_MB = 100
    MAGIC_CHECK_TYPE = "CSV"
    
    def __init__(self):
        self.validator = FileValidator()
    
    async def parse(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Main parse function - performs security checks FIRST.
        
        Args:
            file_content: Raw file bytes from upload
            filename: Original filename from upload
            
        Returns:
            Parsed omics data structure
            
        Raises:
            FileValidationError: If any security check fails
        """
        # SECURITY: Validate file BEFORE any processing
        logger.info(f"Starting Omics file validation: {filename}")
        
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
        # Proceed with normal omics data parsing
        return self._parse_omics_content(file_content, safe_filename, filename)
    
    def _parse_omics_content(self, file_content: bytes, safe_filename: str, original_filename: str) -> Dict[str, Any]:
        """
        Internal omics data parsing logic (existing parsing code).
        Only called after security validation passes.
        """
        try:
            text_content = file_content.decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode omics file as UTF-8: {e}")
            raise ValueError("Omics file must be UTF-8 encoded")
        
        # Auto-detect delimiter
        delimiter = self._detect_delimiter(original_filename, text_content)
        
        try:
            csv_reader = csv.DictReader(StringIO(text_content), delimiter=delimiter)
            rows = []
            
            for i, row in enumerate(csv_reader):
                if i > 50000:  # Limit to 50k rows
                    logger.warning(f"Omics file has >50000 rows, limiting to 50000")
                    break
                rows.append(row)
            
            # Determine omics type
            omics_type = self._determine_omics_type(rows)
            
            return {
                "filename": safe_filename,
                "omics_type": omics_type,
                "row_count": len(rows),
                "columns": list(rows[0].keys()) if rows else [],
                "sample_rows": rows[:10],  # First 10 rows for preview
                "parser_version": "1.0"
            }
        
        except Exception as e:
            logger.error(f"Failed to parse omics file: {e}")
            raise ValueError(f"Failed to parse omics data: {str(e)}")
    
    def _detect_delimiter(self, filename: str, text: str) -> str:
        """Auto-detect delimiter based on filename or content."""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.tsv'):
            return '\t'
        elif filename_lower.endswith('.csv'):
            return ','
        
        # Auto-detect from content
        if '\t' in text[:500]:
            return '\t'
        return ','
    
    def _determine_omics_type(self, rows: List[Dict]) -> str:
        """Determine type of omics data based on content."""
        if not rows:
            return "unknown"
        
        columns = set(rows[0].keys())
        
        # Gene expression
        if any(col.lower() in ['gene_id', 'ensembl_id', 'fpkm', 'tpm'] for col in columns):
            return "gene_expression"
        
        # Proteomics
        if any(col.lower() in ['protein_id', 'uniprot_id', 'intensity', 'abundance'] for col in columns):
            return "proteomics"
        
        # Metabolomics
        if any(col.lower() in ['metabolite_id', 'compound_name', 'mass', 'retention_time'] for col in columns):
            return "metabolomics"
        
        return "generic_tabular"
