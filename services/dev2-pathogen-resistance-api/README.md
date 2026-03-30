# Pathogen & Resistance API

A FastAPI microservice for bacterial genome ingestion and resistance analysis.

## Installation and Setup

### Prerequisites

- Python 3.7+
- FastAPI, Uvicorn, and python-multipart (see requirements.txt)
- FastQC (for quality control)
- SPAdes (for genome assembly)
- Docker or WSL2 (for Windows users running SPAdes)

### Installing Python Dependencies

```bash
pip install -r requirements.txt
```

### Installing FastQC

**Linux:**
```bash
sudo apt-get install fastqc
```

**macOS:**
```bash
brew install fastqc
```

**Or download from:** https://www.bioinformatics.babraham.ac.uk/projects/fastqc/

### Installing SPAdes

#### Option 1: Linux (Recommended)
```bash
sudo apt-get install spades
```

#### Option 2: macOS
```bash
brew install spades
```

#### Option 3: Windows - Using Docker (Recommended)
SPAdes is a Linux-based tool. On Windows, the best approach is Docker:

1. **Install Docker Desktop:**
   - Download: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop
   
2. **Pull SPAdes Docker image:**
   ```bash
   docker pull quay.io/biocontainers/spades:4.3.0--cpu
   ```

3. **Verify SPAdes works:**
   ```bash
   spades.py --version
   ```
   
   The `spades.py` wrapper will automatically detect Docker and use it.

#### Option 4: Windows - Using WSL2
1. **Enable WSL2:**
   ```powershell
   wsl --install
   ```

2. **Install SPAdes in WSL:**
   ```bash
   wsl sudo apt-get install spades
   ```

3. **The wrapper will detect WSL and use it automatically.**

#### Option 5: Windows - Using Conda
1. **Install Miniconda:** https://docs.conda.io/en/latest/miniconda.html

2. **Create conda environment with SPAdes:**
   ```bash
   conda install -c bioconda spades
   ```

3. **Activate the environment before running the API:**
   ```bash
   conda activate spades
   python main.py
   ```

### Running the Server

```bash
# Start the development server
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### Upload Genome

**Endpoint:** `POST /api/v1/pathogens/upload`

**Description:** Upload bacterial genome sequence files in FASTQ, FQ, or BAM format, perform quality control validation using FastQC, and run de novo genome assembly using SPAdes.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `r1_file` (file, required): First read pair file (.fastq, .fq, or .bam)
  - `r2_file` (file, required): Second read pair file (.fastq, .fq, or .bam)
  - `sample_id` (string, required): Sample identifier for tracking

**Response (200 OK):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "assembled"
}
```

**Error Responses:**
- **400 Bad Request:** 
  - Invalid file extensions or missing files: `{"detail": "<error_message>"}`
  - Low quality sequence data: `{"detail": "Low quality sequence data"}`
- **500 Internal Server Error:** 
  - File save operation failed
  - SPAdes assembly failed: `{"detail": "<error_message>"}`

**Processing Pipeline:**

1. **File Validation:** Files are checked for supported extensions (.fastq, .fq, .bam)
2. **FastQC Quality Check:** Both read pair files are validated using FastQC
3. **SPAdes Assembly:** If quality passes, de novo genome assembly is performed
4. **Storage:** Results are saved in `uploads/{job_id}/`

**Automatic Cleanup:**
- Files are deleted if validation fails at any step
- Only successful assemblies are retained

**Prerequisites:**
- FastQC must be installed and available in system PATH
- SPAdes must be installed and available in system PATH

Installation:
```bash
# FastQC
sudo apt-get install fastqc          # Debian/Ubuntu
brew install fastqc                  # macOS

# SPAdes
sudo apt-get install spades          # Debian/Ubuntu
brew install spades                  # macOS
# Or download from: http://spades.bioinf.spbau.ru/spades_download/
```

**Example using curl:**
```bash
curl -X POST http://localhost:8000/api/v1/pathogens/upload \
  -F "r1_file=@sample_R1.fastq" \
  -F "r2_file=@sample_R2.fastq" \
  -F "sample_id=SAMPLE_001"
```

**Example using Python:**
```python
import requests

files = {
    'r1_file': open('sample_R1.fastq', 'rb'),
    'r2_file': open('sample_R2.fastq', 'rb'),
}
data = {'sample_id': 'SAMPLE_001'}

response = requests.post(
    'http://localhost:8000/api/v1/pathogens/upload',
    files=files,
    data=data
)

print(response.json())
```

### Health Check

**Endpoint:** `GET /health`

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

## File Organization

```
services/dev2-pathogen-resistance-api/
├── src/
│   ├── __init__.py
│   └── api/
│       ├── __init__.py
│       └── pathogens.py          # Genome upload, QC, and assembly endpoint
├── uploads/                      # Directory for uploaded files
│   └── {job_id}/
│       ├── r1.<extension>        # First read pair (original format)
│       ├── r2.<extension>        # Second read pair (original format)
│       ├── r1_fastqc.html        # FastQC report for r1
│       ├── r2_fastqc.html        # FastQC report for r2
│       └── assembly/             # SPAdes assembly output
│           ├── contigs.fasta     # Final assembled contigs
│           ├── scaffolds.fasta   # Final assembled scaffolds
│           ├── assembly_graph.fastg
│           └── ...               # Other SPAdes output files
├── main.py                       # FastAPI application entry point
└── requirements.txt              # Python dependencies
```

## File Storage

Uploaded files are stored in the `uploads/{job_id}/` directory:
- `uploads/{job_id}/r1.<extension>` - First read pair
- `uploads/{job_id}/r2.<extension>` - Second read pair

## Allowed File Extensions

- `.fastq` - FASTQ format
- `.fq` - FASTQ format (abbreviated)
- `.bam` - Binary Alignment Map format

## Quality Control and Assembly

### FastQC Validation

Uploaded files are automatically validated using [FastQC](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/) for sequence quality assessment:

1. **Synchronous Processing:** FastQC runs immediately after file upload (no background tasks)
2. **Both Pairs Validated:** Both r1 and r2 files must pass FastQC quality checks
3. **Automatic Cleanup:** Files are deleted if FastQC fails, preventing storage of low-quality data
4. **Clear Error Messages:** If validation fails, the response will indicate: `"Low quality sequence data"`

### SPAdes Genome Assembly

[SPAdes](http://spades.bioinf.spbau.ru/) is used for de novo genome assembly:

1. **Paired-End Assembly:** Both r1 and r2 reads are assembled into contigs and scaffolds
2. **Runs After QC:** Assembly only begins after FastQC validation passes
3. **Output:** Results saved to `uploads/{job_id}/assembly/`
   - `contigs.fasta` - Final assembled contigs
   - `scaffolds.fasta` - Final assembled scaffolds
   - `assembly_graph.fastg` - Assembly graph (FASTG format)
4. **Automatic Cleanup:** If assembly fails, all job files are removed

**Installation:**
```bash
# Debian/Ubuntu
sudo apt-get install spades

# macOS
brew install spades

# Or download from: http://spades.bioinf.spbau.ru/spades_download/
```

## Features

- ✅ Multipart file upload support
- ✅ Validation of file extensions
- ✅ FastQC quality control validation (automatic)
- ✅ SPAdes de novo genome assembly (automatic)
- ✅ Unique job ID generation (UUID4)
- ✅ Automatic directory creation
- ✅ Automatic cleanup on validation failure
- ✅ Proper error handling with HTTP status codes
- ✅ Clean, production-style code
- ✅ Comprehensive docstrings

## Constraints

- No database integration
- No background job queues (Celery)
- No message brokers (Kafka)
- Simple, stateless file storage
- Synchronous processing (FastQC and SPAdes run inline)
- Resistance analysis not yet implemented
- Advanced assembly options (k-mer sizes, etc.) not yet configurable

## Development

The project uses:
- **FastAPI** - Modern web framework for building APIs
- **Uvicorn** - ASGI web server
- **python-multipart** - Multipart form data support

External dependencies:
- **FastQC** - Quality control for sequence data
- **SPAdes** - De novo genome assembly

## Troubleshooting

### SPAdes Command Not Found

**Windows Users:**
If you see "SPAdes is not installed or not found in system PATH", follow these steps:

1. **Check if Docker is installed:**
   ```bash
   docker --version
   ```
   If not installed, install Docker Desktop from https://www.docker.com/products/docker-desktop

2. **Pull the SPAdes Docker image:**
   ```bash
   docker pull quay.io/biocontainers/spades:4.3.0--cpu
   ```

3. **Restart your terminal** and try again

4. **If Docker is not available, enable WSL2:**
   - Open PowerShell as Administrator
   - Run: `wsl --install`
   - Restart your computer
   - In WSL terminal, run: `sudo apt-get install spades`

5. **Verify installation:**
   ```bash
   spades.py --version
   ```

### FastQC Command Not Found

If FastQC is not in your PATH:

**Windows:**
- Add `C:\Stuff\fastqc\FastQC` to your PATH
- Or install: `choco install fastqc` (if Chocolatey is installed)

**Linux:**
```bash
sudo apt-get install fastqc
```

**macOS:**
```bash
brew install fastqc
```

### Assembly Fails with "Low Quality"

If all uploaded sequences are rejected as low quality:
1. Check the sequence files are valid FASTQ/BAM files
2. Verify the reads are long enough (FastQC recommends >36bp)
3. Check that the reads have sufficient coverage
4. Examine the FastQC HTML reports for details
