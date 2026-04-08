"""
File validation module for TheraGenome.
Provides security validation for all file uploads across services.
Single source of truth for file validation logic.
"""

import os
import re
from typing import List


class FileValidationError(Exception):
    """Custom exception for file validation failures."""
    
    def __init__(self, message: str, filename: str = None, reason: str = None):
        """
        Initialize FileValidationError.
        
        Args:
            message: User-friendly error message
            filename: Name of the file that failed validation
            reason: Technical reason for the failure (for logging)
        """
        self.message = message
        self.filename = filename
        self.reason = reason
        super().__init__(self.message)


class FileValidator:
    """
    Central file validation utility for TheraGenome.
    Ensures all uploaded files meet security and format requirements.
    """
    
    # Magic bytes definitions for different file types
    MAGIC_BYTES = {
        'VCF': b'##fileformat=VCF',
        'FASTQ': b'@',
        'CSV': None,  # No magic bytes, but must be printable ASCII
        'XML': [b'<?xml', b'<'],
        'TXT': None,  # Printable ASCII, no null bytes
        'WAV': b'RIFF',
        'MP3': [b'ID3', b'\xff\xfb'],  # ID3 tag or MPEG frame sync
        'WEBM': b'\x1a\x45\xdf\xa3',  # WebM signature
        'OGG': b'OggS',
        'M4A': b'ftyp',
    }
    
    def __init__(self):
        """Initialize FileValidator."""
        pass
    
    def validate_extension(self, filename: str, allowed: List[str]) -> bool:
        """
        Validate file extension against whitelist.
        
        Args:
            filename: Name of the file to validate
            allowed: List of allowed extensions (e.g., ['.vcf', '.vcf.gz'])
            
        Returns:
            True if extension is valid
            
        Raises:
            FileValidationError: If extension is invalid or missing
        """
        if not filename or '.' not in filename:
            raise FileValidationError(
                message=f"File must have an extension",
                filename=filename,
                reason="No file extension found"
            )
        
        # Extract extension (case-insensitive comparison)
        file_lower = filename.lower()
        
        # Check for compound extensions like .vcf.gz
        valid = False
        for allowed_ext in allowed:
            if file_lower.endswith(allowed_ext.lower()):
                valid = True
                break
        
        if not valid:
            allowed_str = ', '.join(allowed)
            raise FileValidationError(
                message=f"File type not allowed. Allowed types: {allowed_str}",
                filename=filename,
                reason=f"Invalid extension. Expected one of: {allowed}"
            )
        
        return True
    
    def validate_size(self, file_bytes: bytes, max_mb: int) -> bool:
        """
        Validate file size does not exceed limit.
        
        Args:
            file_bytes: The file content as bytes
            max_mb: Maximum file size in megabytes
            
        Returns:
            True if file size is valid
            
        Raises:
            FileValidationError: If file exceeds size limit
        """
        max_bytes = max_mb * 1024 * 1024
        actual_size = len(file_bytes)
        
        if actual_size > max_bytes:
            actual_mb = actual_size / (1024 * 1024)
            raise FileValidationError(
                message=f"File size {actual_mb:.1f} MB exceeds maximum of {max_mb} MB",
                reason=f"File too large: {actual_size} bytes > {max_bytes} bytes"
            )
        
        return True
    
    def validate_magic_bytes(self, file_bytes: bytes, file_type: str) -> bool:
        """
        Validate file content matches expected magic bytes for file type.
        
        Args:
            file_bytes: The file content as bytes
            file_type: Type of file (e.g., 'VCF', 'FASTQ', 'CSV', 'XML', 'TXT')
            
        Returns:
            True if magic bytes match expected type
            
        Raises:
            FileValidationError: If magic bytes don't match file type
        """
        if not file_bytes:
            raise FileValidationError(
                message="File is empty",
                reason="No bytes to validate"
            )
        
        # Skip magic byte check for audio files (they're validated by extension + size)
        if file_type in ['WAV', 'MP3', 'WEBM', 'OGG', 'M4A']:
            return True
        
        file_type_upper = file_type.upper()
        
        if file_type_upper == 'VCF':
            # VCF must contain ##fileformat=VCF in first 100 bytes
            header_sample = file_bytes[:100]
            try:
                header_text = header_sample.decode('utf-8', errors='ignore')
                if '##fileformat=VCF' in header_text:
                    return True
            except Exception:
                pass
            
            raise FileValidationError(
                message="File is not a valid VCF file",
                reason="Missing VCF format declaration in header"
            )
        
        elif file_type_upper == 'FASTQ':
            # FASTQ must start with '@'
            if file_bytes[0:1] == b'@':
                return True
            
            raise FileValidationError(
                message="File is not a valid FASTQ file",
                reason="File does not start with '@' character"
            )
        
        elif file_type_upper == 'CSV':
            # CSV must be printable ASCII without excessive null bytes
            return self._validate_printable_text(file_bytes, file_type)
        
        elif file_type_upper == 'XML':
            # XML must start with '<?xml' or '<'
            try:
                text = file_bytes[:100].decode('utf-8', errors='ignore')
                if text.strip().startswith('<?xml') or text.strip().startswith('<'):
                    return True
            except Exception:
                pass
            
            raise FileValidationError(
                message="File is not a valid XML file",
                reason="File does not start with XML declaration or '<'"
            )
        
        elif file_type_upper == 'TXT':
            # TXT must be printable ASCII without null bytes
            return self._validate_printable_text(file_bytes, file_type)
        
        return True
    
    def _validate_printable_text(self, file_bytes: bytes, file_type: str) -> bool:
        """
        Helper to validate that content is printable ASCII text.
        
        Args:
            file_bytes: File content
            file_type: Type of file for error reporting
            
        Returns:
            True if content is valid text
            
        Raises:
            FileValidationError: If content has too many non-text characters
        """
        # Check first 512 bytes for validity
        sample = file_bytes[:512]
        
        # Count non-printable characters (excluding common ones)
        non_printable = 0
        for byte in sample:
            # Allow common text characters: space (32) to ~ (126), tab (9), newline (10), carriage return (13)
            if byte not in (9, 10, 13) and (byte < 32 or byte > 126):
                non_printable += 1
        
        # Allow up to 5% non-printable (for various encodings)
        if non_printable > len(sample) * 0.05:
            raise FileValidationError(
                message=f"File does not appear to be valid {file_type}",
                reason=f"Too many non-printable characters: {non_printable}/{len(sample)}"
            )
        
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and injection attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename with path traversal attempts removed
        """
        if not filename:
            return "file"
        
        # Remove path separators and traversal attempts
        filename = filename.replace('../', '')
        filename = filename.replace('..\\', '')
        filename = filename.replace('./', '')
        filename = filename.replace('.\\', '')
        
        # Keep only safe characters: alphanumeric, hyphen, underscore, dot
        filename = re.sub(r'[^a-zA-Z0-9._\-]', '', filename)
        
        # Remove leading dots (hidden files)
        filename = filename.lstrip('.')
        
        # Truncate to 255 characters (filesystem limit)
        filename = filename[:255]
        
        # Ensure filename isn't empty
        if not filename:
            filename = "file"
        
        return filename
    
    def scan_for_malicious_content(self, file_bytes: bytes) -> bool:
        """
        Scan file content for common malicious patterns.
        
        Args:
            file_bytes: The file content to scan
            
        Returns:
            True if no malicious content found
            
        Raises:
            FileValidationError: If malicious patterns detected
        """
        # Check for null bytes (binary injection)
        if b'\x00' in file_bytes:
            raise FileValidationError(
                message="File contains null bytes (suspicious binary content)",
                reason="Null byte injection attempt detected"
            )
        
        # Convert to string for pattern checking (with error handling)
        try:
            content = file_bytes.decode('utf-8', errors='ignore').lower()
        except Exception:
            # If we can't decode, assume it's suspicious
            raise FileValidationError(
                message="File content cannot be decoded as text",
                reason="Binary file detected when text expected"
            )
        
        # Check for embedded scripts
        malicious_patterns = [
            '<script',
            '<?php',
            '<%',
            'eval(',
            'exec(',
            'system(',
            'shell_exec',
            'passthru',
            'proc_open',
            'popen',
            '__import__',
            'open()',
            'subprocess',
        ]
        
        for pattern in malicious_patterns:
            if pattern.lower() in content:
                raise FileValidationError(
                    message="File contains potentially malicious code",
                    reason=f"Suspicious pattern detected: {pattern}"
                )
        
        # Check for excessively long lines (buffer overflow attempt)
        lines = file_bytes.split(b'\n')
        for i, line in enumerate(lines):
            if len(line) > 10000:
                raise FileValidationError(
                    message="File contains excessively long lines (possible buffer overflow attempt)",
                    reason=f"Line {i+1} has {len(line)} characters (limit: 10000)"
                )
        
        return True
