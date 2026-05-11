"""
PII (Personally Identifiable Information) Filter for TheraGenome.
Detects and redacts sensitive personal information from user input.

Two-layer approach:
1. Regex-based detection (fast, pattern-based)
2. Microsoft Presidio (comprehensive, NLP-based)

Both layers are defensive — never crash, always log safely.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    """Result of PII filtering operation."""
    
    cleaned_text: str
    """Text with PII replaced with [REDACTED]"""
    
    pii_found: bool = False
    """Whether any PII was detected"""
    
    redaction_count: int = 0
    """Number of items redacted"""
    
    types_found: List[str] = field(default_factory=list)
    """Types of PII detected (e.g., ['phone', 'email'])"""
    
    filter_failed: bool = False
    """Whether the filter encountered an error"""
    
    source: str = "text"
    """Source of the text (text, voice, file)"""
    
    language: str = "en"
    """Language of the text"""
    
    def to_audit_log(self) -> Dict[str, Any]:
        """Convert to audit log format (safe, no actual PII)."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "pii_found": self.pii_found,
            "redaction_count": self.redaction_count,
            "types_found": self.types_found,
            "filter_failed": self.filter_failed,
            "source": self.source,
            "language": self.language
        }


class RegexPIIFilter:
    """Regex-based PII detection and redaction (Layer 1)."""
    
    def __init__(self):
        """Initialize regex patterns for PII detection."""
        self.patterns = {
            "phone_number": [
                r'\+?91[\s\-]?[6-9]\d{9}',  # Indian numbers with country code
                r'\b[6-9]\d{9}\b',            # Indian numbers without country code
            ],
            "email": [
                r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b'
            ],
            "aadhaar": [
                r'\b\d{4}\s?\d{4}\s?\d{4}\b'  # 12 digits with optional spaces
            ],
            "date_of_birth": [
                r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b'
            ],
            "name": [
                r'(?i)(my name is|i am|patient name|name:)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'(?i)(patient|doctor|dr\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ],
            "pin_code": [
                r'\b[1-9][0-9]{5}\b'  # Indian PIN codes
            ],
            "passport": [
                r'\b[A-Z]{1}[0-9]{7}\b'  # Passport format
            ],
            "pan_card": [
                r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'  # PAN card format
            ]
        }
    
    def filter_text(self, text: str) -> FilterResult:
        """
        Filter text for PII using regex patterns.
        
        Args:
            text: Text to filter
            
        Returns:
            FilterResult with cleaned text and metadata
        """
        if not text:
            return FilterResult(
                cleaned_text="",
                pii_found=False,
                redaction_count=0,
                types_found=[]
            )
        
        cleaned_text = text
        types_found = set()
        total_redactions = 0
        
        try:
            # Apply each pattern set
            for pii_type, pattern_list in self.patterns.items():
                for pattern in pattern_list:
                    # Find all matches
                    matches = list(re.finditer(pattern, cleaned_text))
                    
                    if matches:
                        types_found.add(pii_type)
                        total_redactions += len(matches)
                        
                        # Replace all matches with [REDACTED]
                        cleaned_text = re.sub(pattern, '[REDACTED]', cleaned_text)
            
            pii_found = len(types_found) > 0
            
            return FilterResult(
                cleaned_text=cleaned_text,
                pii_found=pii_found,
                redaction_count=total_redactions,
                types_found=sorted(list(types_found))
            )
        
        except Exception as e:
            logger.error(f"Regex PII filter error: {str(e)}")
            # Graceful degradation: return original text with error flag
            return FilterResult(
                cleaned_text=text,
                pii_found=False,
                redaction_count=0,
                types_found=[],
                filter_failed=True
            )


class PresidioPIIFilter:
    """Presidio-based PII detection and redaction (Layer 2)."""
    
    def __init__(self, language: str = "en"):
        """
        Initialize Presidio filters.
        
        Args:
            language: Language for analysis ("en", "hi", etc.)
        """
        self.language = language
        self.analyzer = None
        self.anonymizer = None
        self._initialized = False
        self._init_error = None
        
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            
            # Initialize with specified language
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            self._initialized = True
            logger.info(f"Presidio initialized for language: {language}")
        
        except ImportError as e:
            logger.warning(f"Presidio not installed: {str(e)}. Skipping Presidio filter.")
            self._init_error = "Presidio not installed"
        except Exception as e:
            logger.error(f"Presidio initialization error: {str(e)}")
            self._init_error = str(e)
    
    def analyze_and_anonymize(self, text: str, language: str = "en") -> FilterResult:
        """
        Analyze text with Presidio and redact PII.
        
        Args:
            text: Text to analyze
            language: Language code ("en", "hi")
            
        Returns:
            FilterResult with anonymized text and metadata
        """
        if not text:
            return FilterResult(
                cleaned_text="",
                pii_found=False,
                redaction_count=0,
                types_found=[],
                language=language
            )
        
        # If Presidio not available, return as-is
        if not self._initialized:
            logger.debug(f"Presidio unavailable ({self._init_error}), skipping Presidio layer")
            return FilterResult(
                cleaned_text=text,
                pii_found=False,
                redaction_count=0,
                types_found=[],
                language=language,
                filter_failed=False  # Not a failure, just skipped
            )
        
        try:
            # Analyze for PII entities
            results = self.analyzer.analyze(
                text=text,
                language=language,
                entities=[
                    "PERSON",
                    "PHONE_NUMBER",
                    "EMAIL_ADDRESS",
                    "LOCATION",
                    "DATE_TIME",
                    "MEDICAL_LICENSE",
                    "IN_PAN",
                    "IN_AADHAAR"
                ]
            )
            
            if not results:
                return FilterResult(
                    cleaned_text=text,
                    pii_found=False,
                    redaction_count=0,
                    types_found=[],
                    language=language
                )
            
            # Extract entity types found
            types_found = set()
            for result in results:
                # Map Presidio entity types to readable names
                entity_map = {
                    "PERSON": "name",
                    "PHONE_NUMBER": "phone_number",
                    "EMAIL_ADDRESS": "email",
                    "LOCATION": "location",
                    "DATE_TIME": "date_time",
                    "MEDICAL_LICENSE": "medical_license",
                    "IN_PAN": "pan_card",
                    "IN_AADHAAR": "aadhaar"
                }
                readable_type = entity_map.get(result.entity_type, result.entity_type.lower())
                types_found.add(readable_type)
            
            # Anonymize text (replace with [REDACTED])
            anonymized_text = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results
            )
            
            cleaned_text = anonymized_text.text
            pii_found = len(results) > 0
            
            return FilterResult(
                cleaned_text=cleaned_text,
                pii_found=pii_found,
                redaction_count=len(results),
                types_found=sorted(list(types_found)),
                language=language
            )
        
        except Exception as e:
            logger.error(f"Presidio error: {str(e)}")
            # Graceful degradation
            return FilterResult(
                cleaned_text=text,
                pii_found=False,
                redaction_count=0,
                types_found=[],
                language=language,
                filter_failed=True
            )


class PIIFilterPipeline:
    """
    Master PII filter that chains both regex and Presidio layers.
    Runs fast regex first, then comprehensive Presidio analysis.
    """
    
    def __init__(self):
        """Initialize both filter layers."""
        self.regex_filter = RegexPIIFilter()
        self.presidio_filter = PresidioPIIFilter()
        self.audit_logger = self._setup_audit_logging()
    
    def _setup_audit_logging(self) -> logging.Logger:
        """Setup separate logger for PII audit trail."""
        audit_logger = logging.getLogger("pii_audit")
        
        # Only configure if not already configured
        if not audit_logger.handlers:
            try:
                import os
                log_dir = os.path.join(
                    os.path.dirname(__file__),
                    "../../logs"
                )
                os.makedirs(log_dir, exist_ok=True)
                
                handler = logging.FileHandler(
                    os.path.join(log_dir, "pii_audit.log")
                )
                handler.setLevel(logging.INFO)
                
                formatter = logging.Formatter(
                    '%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                handler.setFormatter(formatter)
                audit_logger.addHandler(handler)
                audit_logger.setLevel(logging.INFO)
            
            except Exception as e:
                logger.error(f"Failed to setup audit logging: {str(e)}")
        
        return audit_logger
    
    def process(
        self,
        text: str,
        language: str = "en",
        source: str = "text"
    ) -> FilterResult:
        """
        Process text through both PII filter layers.
        
        Pipeline:
        1. Regex filter (fast, pattern-based)
        2. Presidio filter (comprehensive, NLP-based)
        3. Merge results
        4. Log to audit trail
        5. Return combined result
        
        Args:
            text: Text to filter
            language: Language code ("en", "hi", "es", etc.)
            source: Source of text ("text", "voice", "file")
            
        Returns:
            FilterResult with cleaned text and metadata
        """
        if not text:
            result = FilterResult(
                cleaned_text="",
                pii_found=False,
                redaction_count=0,
                types_found=[],
                source=source,
                language=language
            )
            return result
        
        try:
            # Layer 1: Regex (fast, always runs)
            regex_result = self.regex_filter.filter_text(text)
            
            # Layer 2: Presidio (comprehensive, runs on regex output)
            presidio_result = self.presidio_filter.analyze_and_anonymize(
                regex_result.cleaned_text,
                language=language
            )
            
            # Merge results
            combined_result = FilterResult(
                cleaned_text=presidio_result.cleaned_text,
                pii_found=regex_result.pii_found or presidio_result.pii_found,
                redaction_count=regex_result.redaction_count + presidio_result.redaction_count,
                types_found=sorted(list(set(
                    regex_result.types_found + presidio_result.types_found
                ))),
                source=source,
                language=language,
                filter_failed=regex_result.filter_failed or presidio_result.filter_failed
            )
            
            # Log to audit trail (safe - no actual text content)
            if combined_result.pii_found or combined_result.filter_failed:
                audit_entry = combined_result.to_audit_log()
                self.audit_logger.info(json.dumps(audit_entry))
            
            return combined_result
        
        except Exception as e:
            logger.error(f"PII filter pipeline error: {str(e)}")
            # Graceful degradation: return original text with error flag
            result = FilterResult(
                cleaned_text=text,
                pii_found=False,
                redaction_count=0,
                types_found=[],
                source=source,
                language=language,
                filter_failed=True
            )
            
            # Still log the failure
            audit_entry = result.to_audit_log()
            self.audit_logger.info(json.dumps(audit_entry))
            
            return result
    
    def process_batch(
        self,
        texts: List[str],
        language: str = "en",
        source: str = "text"
    ) -> List[FilterResult]:
        """
        Process multiple texts through the filter pipeline.
        
        Args:
            texts: List of texts to filter
            language: Language code
            source: Source of texts
            
        Returns:
            List of FilterResult objects
        """
        return [
            self.process(text, language=language, source=source)
            for text in texts
        ]


# Singleton instance for easy access
_pipeline_instance = None


def get_pii_filter_pipeline() -> PIIFilterPipeline:
    """Get or create singleton PII filter pipeline."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = PIIFilterPipeline()
    return _pipeline_instance
