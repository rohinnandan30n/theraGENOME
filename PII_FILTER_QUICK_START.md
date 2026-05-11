# PII Filter - Quick Integration Guide

## For Different Modules

### Chat Endpoint Integration

**Location:** `services/dev4-.../src/api/reports.py` or `chat.py`

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from api.middleware import create_pii_filter_middleware

app = FastAPI()
create_pii_filter_middleware(app, language="en")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def handle_chat(request: ChatRequest):
    # Text is automatically filtered by middleware
    message = request.message
    
    # Check if PII was filtered
    from fastapi import Request
    request_obj = None  # Get from context if needed
    
    # Process message (text is already clean)
    response = await llm_service.process(message)
    
    return {
        "response": response,
        # Optional: Add privacy notice if PII was found
        "privacy_notice": "Personal details were removed for privacy."
    }
```

### Voice Input Integration

**Location:** `services/dev4-.../src/voice/stt.py` or `voice/transcription.py`

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.pii_filter import get_pii_filter_pipeline

async def process_audio_input(audio_bytes: bytes, language: str = "en"):
    """
    Process audio through STT, PII filter, then to chat.
    Pipeline: Whisper → PII Filter → LibreTranslate → Chat
    """
    
    # Step 1: Transcribe audio (Whisper)
    transcript = await whisper_transcribe(audio_bytes, language=language)
    print(f"[STT] Transcript: {transcript[:100]}...")
    
    # Step 2: Filter PII from transcript
    pipeline = get_pii_filter_pipeline()
    filter_result = pipeline.process(
        transcript,
        language=language,
        source="voice"
    )
    filtered_text = filter_result.cleaned_text
    
    # Log filtering (audit trail)
    if filter_result.pii_found:
        logger.info(
            f"PII filtered from voice transcript - "
            f"redacted: {filter_result.redaction_count}, "
            f"types: {filter_result.types_found}"
        )
    
    # Step 3: Translate filtered text (if needed)
    translated = await translate_text(filtered_text, target_lang="en")
    
    # Step 4: Process through chat pipeline
    response = await chat_service.process(translated)
    
    # Optional: Notify user about filtering
    if filter_result.pii_found:
        response["pii_notice"] = f"Note: {filter_result.redaction_count} personal details were removed for your privacy."
    
    return response

# Example: Call from API endpoint
@app.post("/voice/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    result = await process_audio_input(
        audio_bytes,
        language=audio.headers.get("X-Language", "en")
    )
    return result
```

### File Upload Integration

**Location:** `services/dev4-.../src/parsers/omics_parser.py`

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from utils.pii_filter import get_pii_filter_pipeline

class OmicsParser:
    async def parse(self, file_content: bytes, filename: str):
        # ... existing file validation ...
        
        # Parse file content (existing logic)
        parsed_data = self._parse_csv_content(file_content, filename)
        
        # NEW: Filter PII from any text fields
        pipeline = get_pii_filter_pipeline()
        
        # Filter clinical notes or free-text fields
        if "clinical_notes" in parsed_data:
            result = pipeline.process(
                parsed_data["clinical_notes"],
                language="en",
                source="file"
            )
            parsed_data["clinical_notes"] = result.cleaned_text
            
            if result.pii_found:
                logger.info(
                    f"Filtered {result.redaction_count} PII items from "
                    f"clinical notes in {filename}"
                )
        
        # Filter other text columns
        for row in parsed_data.get("sample_rows", []):
            for key in ["description", "notes", "comments"]:
                if key in row and isinstance(row[key], str):
                    result = pipeline.process(
                        row[key],
                        source="file"
                    )
                    row[key] = result.cleaned_text
        
        return parsed_data
```

### FastAPI App Setup

**Location:** `services/dev4-.../src/main.py` or `api/app.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware import create_pii_filter_middleware

def create_app() -> FastAPI:
    app = FastAPI(
        title="TheraGenome Dev4 - Core Orchestration",
        version="1.0.0"
    )
    
    # Add standard middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add PII filter middleware (IMPORTANT - must be after CORS)
    create_pii_filter_middleware(app, language="en")
    
    # Import and include routers
    from api import chat_router, voice_router
    app.include_router(chat_router.router)
    app.include_router(voice_router.router)
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Common Patterns

### Pattern 1: Simple Text Filtering

```python
from utils.pii_filter import get_pii_filter_pipeline

# One-liner filtering
pipeline = get_pii_filter_pipeline()
result = pipeline.process("My name is Rahul, call 9876543210")

print(result.cleaned_text)  # "My name is [REDACTED], call [REDACTED]"
print(result.pii_found)     # True
print(result.types_found)   # ["name", "phone_number"]
```

### Pattern 2: Batch Processing

```python
messages = [
    "Hello, I'm John",
    "Call me on 1234567890",
    "The patient has BRCA1"
]

results = pipeline.process_batch(messages, source="text")

for msg, result in zip(messages, results):
    if result.pii_found:
        print(f"Cleaned: {result.cleaned_text}")
```

### Pattern 3: Conditional Logging

```python
result = pipeline.process(user_input)

if result.pii_found:
    logger.info(
        f"PII detected and filtered",
        extra={
            "pii_types": result.types_found,
            "redaction_count": result.redaction_count,
            "language": result.language
        }
    )

# Always safe to use
clean_text = result.cleaned_text
```

### Pattern 4: Voice with Language Detection

```python
# Language might come from user input
language = detect_language(audio_bytes)  # "hi", "en", etc.

result = pipeline.process(
    transcript,
    language=language,
    source="voice"
)
```

### Pattern 5: Error Handling

```python
result = pipeline.process(text)

if result.filter_failed:
    logger.error("PII filter failed, proceeding with unfiltered text")
    # result.cleaned_text contains original unfiltered text
    # This is safe but you should investigate the error

# Use result.cleaned_text regardless
text_for_ai = result.cleaned_text
```

## Testing Your Integration

### Unit Test Template

```python
import pytest
from utils.pii_filter import get_pii_filter_pipeline

@pytest.fixture
def pipeline():
    return get_pii_filter_pipeline()

def test_chat_endpoint_filters_name(pipeline):
    """Test chat removes names."""
    message = "Hi, I'm Rahul Sharma"
    result = pipeline.process(message, source="text")
    
    assert "[REDACTED]" in result.cleaned_text
    assert "Rahul" not in result.cleaned_text
    assert result.pii_found is True

def test_voice_endpoint_filters_phone(pipeline):
    """Test voice filters phone numbers."""
    transcript = "My number is 9876543210"
    result = pipeline.process(transcript, source="voice")
    
    assert "9876543210" not in result.cleaned_text
    assert result.pii_found is True

def test_medical_text_not_filtered(pipeline):
    """Test legitimate medical text passes through."""
    query = "What's treatment for BRCA1 mutations?"
    result = pipeline.process(query, source="text")
    
    assert result.cleaned_text == query
    assert result.pii_found is False
```

### Integration Test

```python
@pytest.mark.asyncio
async def test_chat_endpoint_integration():
    """Test full chat flow with PII filtering."""
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    
    response = client.post("/chat", json={
        "message": "Hi, I'm Rahul Sharma, my phone is 9876543210"
    })
    
    assert response.status_code == 200
    # Middleware should have filtered the message
    assert response.headers.get("X-PII-Filtered") == "true"
    assert response.headers.get("X-Redaction-Count") == "2"
```

## Debugging

### Enable Debug Logging

```python
import logging

# Full debug output
logging.basicConfig(level=logging.DEBUG)

# Or just for PII filter
logger = logging.getLogger("pii_filter")
logger.setLevel(logging.DEBUG)
```

### Check Audit Logs

```bash
# Watch audit logs in real-time
tail -f services/dev4-core-platform-orchestration/logs/pii_audit.log

# Filter by source
grep '"source": "voice"' logs/pii_audit.log | jq '.'

# Count PII events by type
grep types_found logs/pii_audit.log | jq '.types_found' | sort | uniq -c
```

### Manual Testing

```python
from utils.pii_filter import get_pii_filter_pipeline

pipeline = get_pii_filter_pipeline()

test_cases = {
    "phone": "Call me at 9876543210",
    "email": "Email: test@example.com",
    "aadhaar": "My Aadhaar is 1234 5678 9012",
    "name": "Patient name is Rahul Sharma",
    "medical": "The patient has a BRCA1 mutation"
}

for name, text in test_cases.items():
    result = pipeline.process(text)
    print(f"{name:15} | Found: {result.pii_found:5} | Count: {result.redaction_count}")
    if result.pii_found:
        print(f"  {result.cleaned_text}\n")
```

---

**Quick Links:**
- Full Documentation: [PII_FILTER_IMPLEMENTATION.md](PII_FILTER_IMPLEMENTATION.md)
- Test Suite: `tests/unit/test_pii_filter.py`
- Filter Code: `src/utils/pii_filter.py`
- Middleware Code: `src/api/middleware.py`
