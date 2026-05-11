"""
Security and input sanitization utilities for theraGENOME API.

Provides middleware for security headers, input validators to prevent SQL injection and XSS,
and rate limiting utilities.
"""

from fastapi import Request
from fastapi.responses import Response
from typing import Callable
import logging
import re

logger = logging.getLogger(__name__)


# SQL Keywords and injection patterns
SQL_KEYWORDS = {
    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
    'EXEC', 'EXECUTE', 'UNION', 'AND', 'OR', 'WHERE', 'GRANT', 'REVOKE',
    'DECLARE', 'CAST', 'CONVERT', 'SCRIPT', 'JAVASCRIPT'
}

# HTML/XSS tags to block
HTML_TAGS = re.compile(r'<[^>]+>', re.IGNORECASE)

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    re.compile(r'(\s|^)(OR|AND)(\s)+.*=.*', re.IGNORECASE),  # OR/AND 1=1
    re.compile(r'(\s|^)(UNION|SELECT|INSERT|UPDATE|DELETE|DROP)(\s)+', re.IGNORECASE),
    re.compile(r'(-{2}|/\*|\*/|;)', re.IGNORECASE),  # Comment markers and semicolon
    re.compile(r'(xp_|sp_)', re.IGNORECASE),  # Stored procedure execution
]


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    
    Implements best practices for:
    - HSTS (HTTP Strict Transport Security)
    - Content-Type sniffing prevention
    - Clickjacking protection
    - XSS protection
    - Referrer policy
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Add security headers to response."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message["headers"])
                # Strict-Transport-Security: enforces HTTPS
                headers.append((b"strict-transport-security", b"max-age=31536000; includeSubDomains; preload"))
                
                # X-Content-Type-Options: prevents MIME sniffing
                headers.append((b"x-content-type-options", b"nosniff"))
                
                # X-Frame-Options: prevents clickjacking
                headers.append((b"x-frame-options", b"DENY"))
                
                # Content-Security-Policy: restricts resource loading
                headers.append((b"content-security-policy", b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'"))
                
                # Referrer-Policy: controls referrer information
                headers.append((b"referrer-policy", b"no-referrer"))
                
                # Additional security headers
                headers.append((b"x-permitted-cross-domain-policies", b"none"))
                headers.append((b"permissions-policy", b"microphone=(), camera=(), geolocation=()"))
                
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_with_headers)


class InputValidator:
    """Validates and sanitizes user input."""
    
    @staticmethod
    def is_sql_injection_risk(value: str) -> bool:
        """
        Check if string contains SQL injection patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if potential SQL injection detected
        """
        if not isinstance(value, str):
            return False
        
        value_upper = value.upper()
        
        # Check for SQL keywords
        for keyword in SQL_KEYWORDS:
            if f' {keyword} ' in f' {value_upper} ' or value_upper.startswith(keyword):
                for pattern in SQL_INJECTION_PATTERNS:
                    if pattern.search(value):
                        return True
        
        # Check for SQL comment markers
        if '--' in value or '/*' in value or '*/' in value or ';' in value:
            return True
        
        return False
    
    @staticmethod
    def is_xss_risk(value: str) -> bool:
        """
        Check if string contains XSS patterns.
        
        Args:
            value: String to check
            
        Returns:
            True if potential XSS detected
        """
        if not isinstance(value, str):
            return False
        
        # Check for HTML tags
        if HTML_TAGS.search(value):
            return True
        
        # Check for JavaScript event handlers
        if 'javascript:' in value.lower():
            return True
        
        # Check for data URIs with script
        if 'data:text/html' in value.lower():
            return True
        
        return False
    
    @staticmethod
    def sanitize_input(value: str, allow_special: bool = False) -> str:
        """
        Sanitize string input by removing dangerous characters.
        
        Args:
            value: String to sanitize
            allow_special: Allow special characters like @ . -
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return value
        
        # Remove HTML tags
        value = HTML_TAGS.sub('', value)
        
        # Remove control characters
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t')
        
        return value.strip()
    
    @staticmethod
    def validate_string_field(value: str, max_length: int = 255) -> str:
        """
        Validate and sanitize a string field.
        
        Args:
            value: Value to validate
            max_length: Maximum allowed length
            
        Returns:
            Sanitized value
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        if len(value) > max_length:
            raise ValueError(f"String exceeds maximum length of {max_length}")
        
        if len(value.strip()) == 0:
            raise ValueError("String cannot be empty or whitespace only")
        
        # Check for injection attacks
        if InputValidator.is_sql_injection_risk(value):
            raise ValueError("Input contains potential SQL injection patterns")
        
        if InputValidator.is_xss_risk(value):
            raise ValueError("Input contains potential XSS patterns")
        
        return InputValidator.sanitize_input(value)


# Logging utility
def log_security_event(event_type: str, details: str, severity: str = "INFO"):
    """
    Log security events for audit trail.
    
    Args:
        event_type: Type of security event
        details: Event details
        severity: Log level (INFO, WARNING, ERROR)
    """
    getattr(logger, severity.lower())(f"SECURITY_EVENT[{event_type}]: {details}")
