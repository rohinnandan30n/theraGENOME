# File Upload Security - Quick Integration Guide

## For API Endpoints

### FastAPI Example

```python
from fastapi import FastAPI, UploadFile, HTTPException

from services.dev1_genomics_variant_api.src.parsers.vcf_parser import VCFParser
from shared.utils.file_validator import FileValidationError

app = FastAPI()
parser = VCFParser()

@app.post("/api/v1/genomics/upload/vcf")
async def upload_vcf(file: UploadFile):
    """Upload and parse VCF file with security validation"""
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Parse with integrated validation
        # Validation happens FIRST in parser.parse()
        result = await parser.parse(file_content, filename=file.filename)
        
        return {
            "status": "success",
            "data": result
        }
    
    except FileValidationError as e:
        # Log for security auditing
        logger.error(
            f"File upload rejected: {e.filename}",
            extra={"reason": e.reason}
        )
        
        # Return generic 400 error - NEVER expose technical details
        raise HTTPException(
            status_code=400,
            detail="File validation failed. Please check file format and size."
        )
    
    except Exception as e:
        logger.error(f"Upload processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="File processing error"
        )
```

### Flask Example

```python
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest

from services.dev1_genomics_variant_api.src.parsers.vcf_parser import VCFParser
from shared.utils.file_validator import FileValidationError

app = Flask(__name__)
parser = VCFParser()

@app.route("/api/v1/genomics/upload/vcf", methods=["POST"])
def upload_vcf():
    """Upload and parse VCF file with security validation"""
    
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    
    try:
        file_content = file.read()
        result = asyncio.run(parser.parse(file_content, filename=file.filename))
        
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    
    except FileValidationError as e:
        logger.error(f"File upload rejected: {e.filename} - {e.reason}")
        return jsonify({
            "error": "File validation failed",
            "status": 400
        }), 400
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({
            "error": "Processing failed",
            "status": 500
        }), 500
```

## Usage Pattern for Each Service

### 1. VCF Parser (Dev 1)
```python
from services.dev1_genomics_variant_api.src.parsers.vcf_parser import VCFParser

parser = VCFParser()
result = await parser.parse(file_bytes, filename="patient_variants.vcf")
```

### 2. FASTQ Parser (Dev 2)
```python
from services.dev2_pathogen_resistance_api.src.parsers.fastq_parser import FASTQParser

parser = FASTQParser()
result = await parser.parse(file_bytes, filename="reads.fastq")
```

### 3. FAERS Parser (Dev 3)
```python
from services.dev3_drug_safety_toxicity_api.src.parsers.faers_parser import FAERSParser

parser = FAERSParser()
result = await parser.parse(file_bytes, filename="adverse_events.csv")
```

### 4. DrugBank Parser (Dev 3)
```python
from services.dev3_drug_safety_toxicity_api.src.parsers.drugbank_parser import DrugBankParser

parser = DrugBankParser()
result = await parser.parse(file_bytes, filename="drugbank.xml")
```

### 5. Omics Parser (Dev 4)
```python
from services.dev4_core_platform_orchestration.src.parsers.omics_parser import OmicsParser

parser = OmicsParser()
result = await parser.parse(file_bytes, filename="gene_expression.csv")
```

### 6. Audio Parser (Voice)
```python
from services.voice_audio_api.src.parsers.audio_parser import AudioParser

parser = AudioParser()
result = await parser.parse(file_bytes, filename="sample.wav")
```

## Testing Your Integration

### Unit Test Template
```python
import pytest
from services.dev1_genomics_variant_api.src.parsers.vcf_parser import VCFParser
from shared.utils.file_validator import FileValidationError

@pytest.mark.asyncio
async def test_vcf_parser_valid_file():
    """Test parser accepts valid VCF file"""
    parser = VCFParser()
    
    vcf_content = b"""##fileformat=VCFv4.2
##INFO=<ID=DP,Number=1,Type=Integer>
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
chr1\t100\t.\tA\tG\t30\tPASS\tDP=10"""
    
    result = await parser.parse(vcf_content, "test.vcf")
    
    assert result["filename"] == "test.vcf"
    assert result["variant_count"] > 0


@pytest.mark.asyncio
async def test_vcf_parser_invalid_extension():
    """Test parser rejects wrong file type"""
    parser = VCFParser()
    
    with pytest.raises(FileValidationError):
        await parser.parse(b"content", "data.exe")


@pytest.mark.asyncio
async def test_vcf_parser_oversized():
    """Test parser rejects oversized file"""
    parser = VCFParser()
    
    large_file = b"##fileformat=VCFv4.2\n" + b"x" * (60 * 1024 * 1024)
    
    with pytest.raises(FileValidationError):
        await parser.parse(large_file, "huge.vcf")
```

### Integration Test Template
```python
@pytest.mark.asyncio
async def test_api_endpoint_with_valid_file():
    """Test API endpoint with valid file upload"""
    client = TestClient(app)
    
    vcf_data = b"""##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
chr1\t100\t.\tA\tG\t30\tPASS\tDP=10"""
    
    response = client.post(
        "/api/v1/genomics/upload/vcf",
        files={"file": ("test.vcf", vcf_data)}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_api_endpoint_with_malicious_file():
    """Test API endpoint rejects malicious file"""
    client = TestClient(app)
    
    malicious = b"##fileformat=VCFv4.2\n<?php system('rm -rf /'); ?>"
    
    response = client.post(
        "/api/v1/genomics/upload/vcf",
        files={"file": ("evil.vcf", malicious)}
    )
    
    assert response.status_code == 400
    assert "validation" in response.json()["detail"].lower()
```

## Troubleshooting

### "File validation failed" but file seems valid
1. Check file extension (must match whitelist)
2. Verify file size is under limit
3. Check file starts with correct magic bytes
   - VCF: `##fileformat=VCFv`
   - FASTQ: `@`
   - CSV: Printable text
   - XML: `<?xml` or `<`

### "FileValidationError: XXX" - too many details exposed
1. Only catch `FileValidationError` separately
2. Return generic 400 error to client
3. Log full error details server-side
4. Never expose `e.reason` to client

### Parser hangs on large files
1. Check MAX_SIZE_MB limit in parser class
2. File validation should catch oversized files early
3. Large files timeout in size validation, not parsing

## Security Reminders

✅ **DO:**
- Call validators at the START of parse()
- Log full error details server-side
- Return generic errors to clients
- Update parsers when new threats emerge
- Run test suite on every deployment

❌ **DON'T:**
- Skip validation for any uploads
- Trust file extensions alone
- Expose technical errors to clients
- Modify FileValidator per-service
- Store unvalidated files
