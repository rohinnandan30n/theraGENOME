"""
VCF Parser for Dev1 - Genomics Variant API.
Parses Variant Call Format (VCF) files with file upload security validation.
"""

import logging
from typing import Dict, List, Any

# Security: Import file validator
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))
from shared.utils.file_validator import FileValidator, FileValidationError

logger = logging.getLogger(__name__)


class VCFParser:
    """Parser for VCF (Variant Call Format) files with security validation."""
    
    # VCF Parser configuration
    ALLOWED_EXTENSIONS = [".vcf", ".vcf.gz", ".txt"]
    MAX_SIZE_MB = 50
    MAGIC_CHECK_TYPE = "VCF"
    
    # Standard VCF header fields
    REQUIRED_FIELDS = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO', 'FORMAT']
    FIXED_FIELDS = ['CHROM', 'POS', 'REF', 'ALT', 'QUAL', 'INFO']
    
    def __init__(self):
        self.header_lines = []
        self.field_indices = {}
        self.validator = FileValidator()
    
    async def parse(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Main parse function - performs security checks FIRST.
        
        Args:
            file_content: Raw file bytes from upload
            filename: Original filename from upload
            
        Returns:
            Parsed VCF data structure
            
        Raises:
            FileValidationError: If any security check fails
        """
        # SECURITY: Validate file BEFORE any processing
        logger.info(f"Starting VCF file validation: {filename}")
        
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
        # Proceed with normal VCF parsing
        return self._parse_vcf_content(file_content, safe_filename)
    
    def _parse_vcf_content(self, file_content: bytes, safe_filename: str) -> Dict[str, Any]:
        """
        Internal VCF parsing logic (existing parsing code).
        Only called after security validation passes.
        """
        try:
            text_content = file_content.decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode VCF file as UTF-8: {e}")
            raise ValueError("VCF file must be UTF-8 encoded")
        
        lines = text_content.strip().split('\n')
        
        # Validate VCF format
        if not self._validate_vcf_format(lines):
            raise ValueError("Invalid VCF file format")
        
        # Parse header and data
        variants = []
        header_idx = self._find_header_line(lines)
        
        if header_idx >= 0:
            header_line = lines[header_idx]
            self.field_indices = self.parse_header(header_line)
            
            # Parse variant lines
            for idx in range(header_idx + 1, len(lines)):
                if lines[idx].strip() and not lines[idx].startswith('#'):
                    variant = self._parse_variant_line(lines[idx])
                    if variant:
                        variants.append(variant)
        
        return {
            "filename": safe_filename,
            "variant_count": len(variants),
            "variants": variants,
            "header_info": self._extract_header_info(lines[:header_idx + 1])
        }
    
    def _validate_vcf_format(self, lines: List[str]) -> bool:
        """Validate VCF file format."""
        if not lines or not lines[0].startswith('##fileformat=VCFv'):
            logger.error("Invalid VCF file: missing or incorrect fileformat declaration")
            return False
        return True
    
    def _find_header_line(self, lines: List[str]) -> int:
        """Find the #CHROM header line."""
        for idx, line in enumerate(lines):
            if line.startswith('#CHROM'):
                return idx
        return -1
    
    def parse_header(self, header_line: str) -> Dict[str, int]:
        """Parse VCF header line to get field indices."""
        fields = header_line.lstrip('#').split('\t')
        
        # Validate required fields
        for required_field in self.FIXED_FIELDS:
            if required_field not in fields:
                raise ValueError(f"Missing required VCF field: {required_field}")
        
        return {field: idx for idx, field in enumerate(fields)}
    
    def _parse_variant_line(self, line: str) -> Dict[str, Any]:
        """Parse a variant data line."""
        try:
            fields = line.split('\t')
            if len(fields) < len(self.FIXED_FIELDS):
                return None
            
            return {
                "chrom": fields[self.field_indices.get('CHROM', 0)],
                "pos": fields[self.field_indices.get('POS', 1)],
                "id": fields[self.field_indices.get('ID', 2)],
                "ref": fields[self.field_indices.get('REF', 3)],
                "alt": fields[self.field_indices.get('ALT', 4)],
                "qual": fields[self.field_indices.get('QUAL', 5)],
                "info": fields[self.field_indices.get('INFO', 7)] if len(fields) > 7 else ""
            }
        except (IndexError, ValueError) as e:
            logger.warning(f"Failed to parse variant line: {e}")
            return None
    
    def _extract_header_info(self, header_lines: List[str]) -> Dict[str, str]:
        """Extract metadata from VCF header."""
        metadata = {}
        for line in header_lines:
            if line.startswith('##'):
                parts = line[2:].split('=', 1)
                if len(parts) == 2:
                    metadata[parts[0]] = parts[1]
        return metadata
