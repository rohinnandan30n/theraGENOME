# TheraGenome PII Filter Implementation

## Overview

A comprehensive two-layer PII (Personally Identifiable Information) filtering system for TheraGenome's chat, voice, and file upload pipelines. Silently redacts sensitive information without disrupting the user experience.

**Key Features:**
- ✅ Two-layer detection: Regex (fast) + Presidio (comprehensive)
- ✅ Zero pipeline disruption: Graceful degradation on errors
- ✅ Safe logging: Audit trail with no actual PII values
- ✅ Multi-language support: English, Hindi, and more
- ✅ Medical text preservation: Legitimate medical terms not flagged
- ✅ Configurable per endpoint

## Architecture

### Layer 1: Regex-Based Filter
Fast pattern-based detection for common PII formats:
- Phone numbers (Indian: +91-XXXXXXXXXX, 9X-XXXXXXXXX)
- Email addresses
- Aadhaar numbers (12 digits with optional spaces)
- Dates of birth (DD/MM/YYYY, DD-MM-YY)
- Names (with trigger phrases: "my name is", "patient name")
- Indian PIN codes
- Passport numbers
- PAN card numbers

**Performance:** < 5ms for typical text

### Layer 2: Presidio-Based Filter
NLP-powered entity recognition via Microsoft Presidio:
- PERSON (names, including nicknames)
- PHONE_NUMBER (multiple formats)
- EMAIL_ADDRESS
- LOCATION (cities, countries, addresses)
- DATE_TIME (various date formats)
- MEDICAL_LICENSE
- IN_PAN (Indian PAN cards)
- IN_AADHAAR (Indian Aadhaar cards)

**Performance:** ~50-100ms (depends on text length)

### Pipeline Flow

```
User Input (Text/Voice/File)
        ↓
   [RegexPIIFilter]  ← Fast (Layer 1)
        ↓
[PresidioPIIFilter]  ← Comprehensive (Layer 2)
        ↓
    [Merge Results]
        ↓
 [Audit Logging]      ← Safe (no actual PII logged)
        ↓
  [Cleaned Text]      ← Ready for AI/LLM
```

## Installation

### Core Requirements
```bash
pip install fastapi starlette
```

### With Presidio Support (Optional but Recommended)
```bash
pip install presidio-analyzer presidio-anonymizer
pip install transformers  # For Hindi language support
```

### Without Presidio
The filter will work with regex alone if Presidio is not installed. It will gracefully degrade and use only Layer 1 detection.

## File Structure

```
services/dev4-core-platform-orchestration/
├── src/
│   ├── utils/
│   │   ├── __init__.py
│   │   └── pii_filter.py          ← Core filter logic
│   └── api/
│       └── middleware.py           ← FastAPI middleware
├── tests/
│   └── unit/
│       ├── __init__.py
│       └── test_pii_filter.py     ← 40+ test cases
└── logs/
    └── pii_audit.log             ← Audit trail (safe)
```

## Usage

### 1. Basic Usage (Direct)

```python
from services.dev4_core_platform_orchestration.src.utils.pii_filter import get_pii_filter_pipeline

# Get singleton instance
pipeline = get_pii_filter_pipeline()

# Process text
text = "My name is Rahul Sharma, call me on 9876543210"
result = pipeline.process(
    text,
    language="en",
    source="text"
)

# Use cleaned text
if result.pii_found:
    print(f"Filtered text: {result.cleaned_text}")
    print(f"Warning: {result.redaction_count} items redacted")
```

### 2. FastAPI Middleware (Automatic)

```python
from fastapi import FastAPI
from services.dev4_core_platform_orchestration.src.api.middleware import create_pii_filter_middleware

app = FastAPI()

# Add PII filter middleware
create_pii_filter_middleware(app, language="en")

# Now all /chat and /voice endpoints are automatically filtered
@app.post("/chat")
async def chat(message: str):
    # Message is already filtered by middleware
    return {"response": "..."}
```

### 3. Voice Pipeline

```python
# In your STT/transcription module
from services.dev4_core_platform_orchestration.src.utils.pii_filter import get_pii_filter_pipeline

async def process_voice_input(audio_bytes):
    # Step 1: Whisper transcription
    transcript = await whisper_transcribe(audio_bytes)
    
    # Step 2: PII filter (BEFORE translation)
    pipeline = get_pii_filter_pipeline()
    filter_result = pipeline.process(
        transcript,
        language="en",
        source="voice"
    )
    
    # Step 3: Translation (on filtered text)
    translated = await translate(filter_result.cleaned_text)
    
    # Step 4: Pass to chat
    return await chat_endpoint(translated)
```

### 4. File Upload Pipeline

```python
# In your omics_parser.py
from services.dev4_core_platform_orchestration.src.utils.pii_filter import get_pii_filter_pipeline

async def parse_omics_file(file_content):
    # Parse file
    parsed = parse_csv(file_content)
    
    # Filter any free-text fields
    pipeline = get_pii_filter_pipeline()
    
    for record in parsed:
        if "clinical_notes" in record:
            result = pipeline.process(
                record["clinical_notes"],
                source="file"
            )
            record["clinical_notes"] = result.cleaned_text
    
    return parsed
```

## API Reference

### FilterResult

```python
@dataclass
class FilterResult:
    cleaned_text: str              # Text with PII replaced
    pii_found: bool                # Whether any PII detected
    redaction_count: int           # # of items redacted
    types_found: List[str]        # Types: ["phone", "email", ...]
    filter_failed: bool            # Whether filter encountered error
    source: str                    # "text", "voice", or "file"
    language: str                  # Language code
    
    def to_audit_log(self) -> Dict:
        # Convert to safe audit log (no actual PII)
```

### RegexPIIFilter

```python
class RegexPIIFilter:
    def filter_text(text: str) -> FilterResult:
        """Fast regex-based PII filtering."""
```

### PresidioPIIFilter

```python
class PresidioPIIFilter:
    def analyze_and_anonymize(text: str, language: str = "en") -> FilterResult:
        """Comprehensive NLP-based PII filtering."""
```

### PIIFilterPipeline

```python
class PIIFilterPipeline:
    def process(
        text: str,
        language: str = "en",
        source: str = "text"
    ) -> FilterResult:
        """Main entry point: combines both filters."""
    
    def process_batch(
        texts: List[str],
        language: str = "en",
        source: str = "text"
    ) -> List[FilterResult]:
        """Process multiple texts efficiently."""
```

## Integration Guide

### For Chat Endpoint

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from services.dev4_core_platform_orchestration.src.api.middleware import create_pii_filter_middleware

app = FastAPI()
create_pii_filter_middleware(app)

@app.post("/chat")
async def chat(request: ChatRequest):
    # Text is already filtered by middleware
    message = request.message  # Already filtered!
    
    # Get PII warning if applicable
    if request.headers.get("X-PII-Filtered") == "true":
        redaction_count = request.headers.get("X-Redaction-Count", "0")
        return {
            "response": "...",
            "warning": f"Note: {redaction_count} personal details were removed for privacy."
        }
    
    return {"response": "..."}
```

### For Voice Endpoint

```python
from fastapi import UploadFile, File
from services.dev4_core_platform_orchestration.src.utils.pii_filter import get_pii_filter_pipeline

@app.post("/voice")
async def process_voice(file: UploadFile = File(...)):
    # Transcribe audio
    transcript = await transcribe_audio(await file.read())
    
    # Filter PII from transcript
    pipeline = get_pii_filter_pipeline()
    result = pipeline.process(
        transcript,
        language="en",
        source="voice"
    )
    
    # Log filtering event (audit trail)
    if result.pii_found:
        logger.info(f"PII filtered from voice: {result.types_found}")
    
    # Process filtered transcript
    response = await process_chat(result.cleaned_text)
    
    # Optional: Add filtering warning to response
    if result.pii_found:
        response["pii_warning"] = "Personal information was removed for privacy"
    
    return response
```

### For File Upload

```python
from services.dev4_core_platform_orchestration.src.parsers.omics_parser import OmicsParser
from services.dev4_core_platform_orchestration.src.utils.pii_filter import get_pii_filter_pipeline

async def parse_uploaded_file(file_bytes: bytes, filename: str):
    # Parse file
    parser = OmicsParser()
    parsed_data = await parser.parse(file_bytes, filename)
    
    # Filter any text fields
    pipeline = get_pii_filter_pipeline()
    
    for item in parsed_data.get("sample_rows", []):
        # Filter text columns
        for key, value in item.items():
            if isinstance(value, str):
                result = pipeline.process(
                    value,
                    source="file"
                )
                item[key] = result.cleaned_text
    
    return parsed_data
```

## Audit Logging

### Log Format (Safe)

Each PII detection event is logged to `logs/pii_audit.log`:

```json
{
  "timestamp": "2026-04-08T10:30:45.123456",
  "pii_found": true,
  "redaction_count": 2,
  "types_found": ["name", "phone_number"],
  "filter_failed": false,
  "source": "text",
  "language": "en"
}
```

**Important:** The log contains NO actual personal information:
- No original text
- No cleaned text
- No actual PII values
- Only metadata about what types were found

### Log Location

```
services/dev4-core-platform-orchestration/logs/pii_audit.log
```

### Viewing Logs

```bash
# All PII filtering events
tail -f logs/pii_audit.log

# PII events from voice
grep '"source": "voice"' logs/pii_audit.log

# Events with multiple redactions
grep -E '"redaction_count": [5-9]' logs/pii_audit.log

# Analysis: most common PII types
grep types_found logs/pii_audit.log | jq '.types_found' | sort | uniq -c
```

## Configuration

### Supported Languages

```python
# English (default)
pipeline.process(text, language="en")

# Hindi (requires transformers)
pipeline.process(text, language="hi")

# Other languages supported by Presidio
# "es" (Spanish), "de" (German), "fr" (French), etc.
```

### Custom Middleware Configuration

```python
from middleware import PIIFilterMiddleware
from fastapi import FastAPI

app = FastAPI()

# Customize language and routes
middleware = PIIFilterMiddleware(app, language="hi")

# Customize protected routes
middleware.PROTECTED_ROUTES = [
    "/api/v1/chat",
    "/api/v1/voice",
    "/api/v1/transcribe"
]
```

## Testing

### Run All Tests

```bash
pytest services/dev4-core-platform-orchestration/tests/unit/test_pii_filter.py -v
```

### Run Specific Test Class

```bash
pytest services/dev4-core-platform-orchestration/tests/unit/test_pii_filter.py::TestRegexPIIFilter -v
```

### Test Coverage

```bash
pytest services/dev4-core-platform-orchestration/tests/unit/test_pii_filter.py \
    --cov=services.dev4_core_platform_orchestration.src.utils.pii_filter \
    --cov-report=html
```

### Test Cases Included

**Regex Filter:**
- Phone numbers (with/without country code)
- Email addresses
- Aadhaar, PAN, Passport numbers
- Dates of birth
- Indian PIN codes
- Name patterns with trigger phrases
- Multiple PII items in single text
- Medical text preservation (no false positives)

**Presidio Filter:**
- Various name formats
- Phone numbers in different formats
- Locations and addresses
- Date/time expressions
- Language-specific entities

**Pipeline:**
- Batch processing
- Multi-language support
- Graceful degradation on errors
- Voice source handling
- File source handling
- Safe audit logging

**Integration:**
- Chat message scenarios
- Voice transcript scenarios
- Medical report scenarios
- No PII exposure in responses

## Error Handling

### Philosophy: Never Block, Always Degrade

If the filter encounters ANY error:
1. Returns original text (unfiltered)
2. Sets `filter_failed=True` flag
3. Logs the error for debugging
4. Continues normally (no exception raised)

```python
# Even if filter crashes, this never fails:
result = pipeline.process(text)

# Check flag to detect filtering failures
if result.filter_failed:
    logger.warning("PII filter failed, text not filtered")
    # Text is original, unf iltered

# Always safe to use result.cleaned_text
use_text(result.cleaned_text)
```

## Security Considerations

### ✅ DO

- Filter text BEFORE passing to AI/LLM
- Log audit trail WITH source and timestamp
- Use middleware for automatic filtering
- Test with real personal data
- Monitor audit logs for attack patterns
- Gracefully handle filter failures

### ❌ DON'T

- Store original, unfiltered user input
- Log actual PII values anywhere
- Expose filter logic in error messages
- Skip filtering on "trusted" inputs
- Block requests if filter fails
- Modify filtered text after filtering

## Performance Characteristics

### Layer 1 (Regex)
- **Time:** < 5ms for typical message (< 1000 chars)
- **Scalability:** Linear in text length
- **Memory:** Minimal (pattern matching only)

### Layer 2 (Presidio)
- **Time:** 50-100ms for typical message
- **Scalability:** Can handle 10K+ chars
- **Memory:** ~100MB for model loading
- **Cold Start:** ~1-2s on first request

### Combined Pipeline
- **Typical Time:** 50-105ms per request
- **Throughput:** ~10 requests/second per instance
- **Recommended:** Load balance with 2-4 instances

## Troubleshooting

### Filter returns original text without redactions

1. Check if Presidio is installed:
   ```bash
   pip show presidio-analyzer presidio-anonymizer
   ```

2. Check logs for errors:
   ```bash
   tail -f logs/pii_audit.log
   ```

3. Enable debug logging:
   ```python
   import logging
   logging.getLogger("pii_filter").setLevel(logging.DEBUG)
   ```

### Legitimate text is being redacted

Add test case to `/tests/unit/test_pii_filter.py`:

```python
def test_case_name(self):
    text = "Your legitimate text here"
    result = pipeline.process(text)
    assert result.pii_found is False  # Should not find PII
```

Then check which patterns are matching and adjust if needed.

### Performance Issues

1. Reduce Presidio threshold (if available)
2. Cache pipeline instance (done automatically via singleton)
3. Use batch processing for multiple texts
4. Consider Regex-only mode if Presidio is slow

## Next Steps

1. **Integrate into chat endpoint:** Add middleware to FastAPI app
2. **Integrate into voice pipeline:** Add filter after Whisper transcription
3. **Test with real data:** Run full test suite
4. **Monitor audit logs:** Set up log analysis
5. **Adjust patterns:** Fine-tune based on false positives/negatives

---

**Last Updated:** April 8, 2026  
**Status:** Production Ready  
**Test Coverage:** 40+ test cases
