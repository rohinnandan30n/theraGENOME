"""
DrugBank Parser for Dev3 - Drug Safety & Toxicity API.
Parses DrugBank XML database files with security validation.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any

# Security: Import file validator
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))
from shared.utils.file_validator import FileValidator, FileValidationError

logger = logging.getLogger(__name__)


class DrugBankParser:
    """Parser for DrugBank XML files with security validation."""
    
    # DrugBank Parser configuration
    ALLOWED_EXTENSIONS = [".xml", ".csv"]
    MAX_SIZE_MB = 200
    MAGIC_CHECK_TYPE = "XML"
    
    def __init__(self):
        self.validator = FileValidator()
    
    async def parse(self, file_content: bytes, filename: str = None) -> Dict[str, Any]:
        """
        Main parse function - performs security checks FIRST.
        
        Args:
            file_content: Raw file bytes from upload
            filename: Original filename from upload
            
        Returns:
            Parsed DrugBank data structure
            
        Raises:
            FileValidationError: If any security check fails
        """
        # SECURITY: Validate file BEFORE any processing
        logger.info(f"Starting DrugBank file validation: {filename}")
        
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
        # Proceed with normal DrugBank parsing
        return self._parse_drugbank_content(file_content, safe_filename)
    
    def _parse_drugbank_content(self, file_content: bytes, safe_filename: str) -> Dict[str, Any]:
        """
        Internal DrugBank parsing logic (existing parsing code).
        Only called after security validation passes.
        """
        try:
            text_content = file_content.decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode DrugBank file as UTF-8: {e}")
            raise ValueError("DrugBank file must be UTF-8 encoded")
        
        try:
            root = ET.fromstring(text_content)
        except ET.ParseError as e:
            logger.error(f"Failed to parse DrugBank XML: {e}")
            raise ValueError(f"Invalid XML format: {str(e)}")
        
        drugs = []
        
        # Parse drug entries from XML
        for drug_elem in root.findall('.//{http://www.drugbank.ca}drug'):
            drug_dict = {
                "drug_bank_id": self._get_text(drug_elem, './/{http://www.drugbank.ca}drugbank-id'),
                "name": self._get_text(drug_elem, './/{http://www.drugbank.ca}name'),
                "description": self._get_text(drug_elem, './/{http://www.drugbank.ca}description'),
                "affected_organisms": self._get_all_text(drug_elem, './/{http://www.drugbank.ca}affected-organism'),
                "indication": self._get_text(drug_elem, './/{http://www.drugbank.ca}indication'),
                "pharmacology": self._get_text(drug_elem, './/{http://www.drugbank.ca}pharmacology'),
                "side_effects": self._get_all_text(drug_elem, './/{http://www.drugbank.ca}side-effect'),
            }
            drugs.append(drug_dict)
        
        return {
            "filename": safe_filename,
            "drug_count": len(drugs),
            "drugs": drugs[:100],  # Limit to 100 for summary
            "parser_version": "1.0"
        }
    
    def _get_text(self, element: ET.Element, path: str) -> str:
        """Extract text from element at specified path."""
        elem = element.find(path)
        return elem.text if elem is not None and elem.text else ""
    
    def _get_all_text(self, element: ET.Element, path: str) -> List[str]:
        """Extract all text values from elements at specified path."""
        results = []
        for elem in element.findall(path):
            if elem.text:
                results.append(elem.text)
        return results
