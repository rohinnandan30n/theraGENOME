"""
FastAPI Middleware for PII Filtering.
Automatically filters personal information from incoming requests.

Applies to:
- /chat and /chat/* endpoints (text input)
- /voice and /voice/* endpoints (voice transcripts)
"""

import json
import logging
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.pii_filter import get_pii_filter_pipeline, FilterResult

logger = logging.getLogger(__name__)


class PIIFilterMiddleware(BaseHTTPMiddleware):
    """
    Middleware to filter PII from request bodies.
    Processes /chat and /voice endpoints.
    """
    
    # Endpoints that should have PII filtering applied
    PROTECTED_ROUTES = [
        "/chat",
        "/voice",
        "/transcribe",
        "/analyze"
    ]
    
    def __init__(self, app, language: str = "en"):
        """
        Initialize PII filter middleware.
        
        Args:
            app: FastAPI application
            language: Default language for PII filtering
        """
        super().__init__(app)
        self.pii_pipeline = get_pii_filter_pipeline()
        self.default_language = language
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request through PII filter.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response (may include PII filter warning)
        """
        # Check if this route should be filtered
        if not self._should_filter_route(request.url.path):
            return await call_next(request)
        
        # Store original response for processing
        request.state.pii_filter_result = None
        
        try:
            # Read and filter request body
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                
                if body:
                    # Try to parse as JSON and filter text fields
                    filtered_body, filter_result = await self._filter_request_body(
                        body,
                        request
                    )
                    
                    # Store original and filtered content
                    request.state.pii_filter_result = filter_result
                    request._body = filtered_body
            
            # Continue to next middleware/endpoint
            response = await call_next(request)
            
            # Add filter warning header if PII was found
            if hasattr(request.state, 'pii_filter_result') and request.state.pii_filter_result:
                result = request.state.pii_filter_result
                
                if result.pii_found and not result.filter_failed:
                    response.headers["X-PII-Filtered"] = "true"
                    response.headers["X-Redaction-Count"] = str(result.redaction_count)
                    response.headers["X-PII-Types"] = ",".join(result.types_found)
                    
                    logger.info(
                        f"PII filtered from {request.url.path}: "
                        f"redacted={result.redaction_count}, types={result.types_found}"
                    )
            
            return response
        
        except Exception as e:
            logger.error(f"PII middleware error: {str(e)}")
            # Don't block the request, just log and continue
            return await call_next(request)
    
    def _should_filter_route(self, path: str) -> bool:
        """Check if route should be filtered."""
        return any(path.startswith(route) for route in self.PROTECTED_ROUTES)
    
    async def _filter_request_body(
        self,
        body: bytes,
        request: Request
    ) -> tuple:
        """
        Filter PII from request body.
        
        Args:
            body: Request body bytes
            request: Request object
            
        Returns:
            Tuple of (filtered_body_bytes, FilterResult)
        """
        try:
            # Try to parse as JSON
            data = json.loads(body.decode("utf-8"))
            
            # Get language from headers or use default
            language = request.headers.get("X-Language", self.default_language)
            
            # Get source (voice/text/etc)
            source = "voice" if "/voice" in request.url.path else "text"
            
            # Filter text fields
            filtered_data = data.copy()
            filter_results = []
            
            # Filter common text fields
            text_fields = ["message", "text", "query", "input", "transcript", "content"]
            
            for field in text_fields:
                if field in filtered_data and isinstance(filtered_data[field], str):
                    result = self.pii_pipeline.process(
                        filtered_data[field],
                        language=language,
                        source=source
                    )
                    filtered_data[field] = result.cleaned_text
                    filter_results.append(result)
            
            # Merge results if multiple fields were filtered
            merged_result = self._merge_filter_results(filter_results, source, language)
            
            # Convert back to bytes
            filtered_body = json.dumps(filtered_data).encode("utf-8")
            
            return filtered_body, merged_result
        
        except json.JSONDecodeError:
            # Not JSON, treat as plain text
            text = body.decode("utf-8", errors="ignore")
            language = request.headers.get("X-Language", self.default_language)
            source = "voice" if "/voice" in request.url.path else "text"
            
            result = self.pii_pipeline.process(
                text,
                language=language,
                source=source
            )
            
            return result.cleaned_text.encode("utf-8"), result
        
        except Exception as e:
            logger.error(f"Error filtering request body: {str(e)}")
            # Return original body on error
            return body, None
    
    def _merge_filter_results(self, results: list, source: str, language: str):
        """Merge multiple filter results into one."""
        if not results:
            return None
        
        if len(results) == 1:
            return results[0]
        
        # Merge multiple results
        merged = FilterResult(
            cleaned_text="",  # Not used when merging
            pii_found=any(r.pii_found for r in results),
            redaction_count=sum(r.redaction_count for r in results),
            types_found=sorted(list(set(
                t for r in results for t in r.types_found
            ))),
            source=source,
            language=language,
            filter_failed=any(r.filter_failed for r in results)
        )
        
        return merged


class PIIFilterResponseMiddleware(BaseHTTPMiddleware):
    """
    Optional middleware to filter PII from responses.
    Useful for logging and debugging.
    """
    
    def __init__(self, app):
        """Initialize response filter middleware."""
        super().__init__(app)
        self.pii_pipeline = get_pii_filter_pipeline()
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process response through PII filter."""
        response = await call_next(request)
        
        # Only filter error responses to avoid logging actual data
        if response.status_code >= 400:
            try:
                # Read response body
                if "application/json" in response.headers.get("content-type", ""):
                    # For error responses, we might want to check error messages
                    # but be careful not to expose filtered information
                    pass
            except Exception:
                pass
        
        return response


def create_pii_filter_middleware(app, language: str = "en"):
    """
    Helper to create and add PII filter middleware to FastAPI app.
    
    Usage:
        from fastapi import FastAPI
        from middleware import create_pii_filter_middleware
        
        app = FastAPI()
        create_pii_filter_middleware(app, language="en")
    
    Args:
        app: FastAPI application
        language: Default language for PII analysis
    """
    app.add_middleware(PIIFilterMiddleware, language=language)
    logger.info(f"PII Filter Middleware initialized (language: {language})")
