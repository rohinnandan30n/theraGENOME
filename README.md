# theraGENOME - Genomics & Variant API

Human Genetics AI • Variant Interpreter Module

## Task 1.1: Genomic Data Ingestion Pipeline

### Overview
This module implements a FastAPI-based genomic data ingestion pipeline that accepts, validates, parses, and stores genomic data files (VCF, FASTQ, BAM formats).

### Features

#### File Upload Endpoint
- **Endpoint**: `POST /api/v1/ingestion/upload`
- **Supported Formats**: VCF, FASTQ, BAM
- **Functionality**:
  - Accept file uploads with validation
  - Validate file format and integrity
  - Parse genomic data into structured records
  - Store data in PostgreSQL database
  - Publish ingestion events to Kafka message bus
  - Return asynchronous job ID for tracking

#### Genomic Data Processing
- **VCF Parser**: Extracts variant records with the following fields:
  - CHROM (chromosome)
  - POS (position)
  - REF (reference allele)
  - ALT (alternate allele)
  - QUAL (quality score)
  - INFO (additional information)

#### Validation Layer
- File format validation
- File integrity checks
- VCF header validation
- Variant record validation
- Error handling and reporting

#### Data Storage
- **PostgreSQL**: Stores parsed variant records
- **S3-Compatible Storage**: Archives raw uploaded files
- Structured schema with indexing for efficient queries

#### Event Publishing
- **Kafka Topic**: `raw_variants`
- **Event Format**: JSON with metadata
- Includes variant count, status, timestamps, and error details

### Project Structure

```
theraGENOME/
├── src/
│   ├── api/
│   │   ├── ingestion.py      # Upload and ingestion endpoints
│   │   └── schemas.py        # Request/response models
│   ├── db/
│   │   ├── connection.py     # Database connection management
│   │   └── repository.py     # Data access layer
│   ├── parsers/
│   │   └── vcf_parser.py     # VCF file parser
│   ├── messaging/
│   │   └── kafka_producer.py # Kafka event publisher
│   ├── storage/
│   │   └── file_storage.py   # File storage management
│   ├── schemas/
│   │   └── variant_schema.sql # Database schema
│   ├── config.py             # Configuration management
│   └── main.py               # FastAPI application
├── requirements.txt          # Python dependencies
├── .env.example             # Environment configuration template
└── README.md               # This file
```

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rohinnandan30n/theraGENOME.git
   cd theraGENOME
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Configuration

Set up your `.env` file with the following variables:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=genomic_db
DB_USER=postgres
DB_PASSWORD=your_password

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_RAW_VARIANTS=raw_variants

# Storage
STORAGE_PATH=./uploads
MAX_FILE_SIZE=5242880

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
```

### Running the Application

```bash
python -m src.main
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### API Endpoints

#### Health Check
```
GET /health
```

#### Upload Genomic File
```
POST /api/v1/ingestion/upload
Content-Type: multipart/form-data

Parameters:
- file: VCF, FASTQ, or BAM file
- validate_only: boolean (optional, default: False)

Response:
{
  "job_id": "uuid",
  "filename": "string",
  "status": "COMPLETED|PROCESSING|FAILED",
  "variant_count": integer,
  "message": "string"
}
```

#### Get Job Status
```
GET /api/v1/ingestion/status/{job_id}

Response:
{
  "job_id": "uuid",
  "filename": "string",
  "status": "string",
  "variant_count": integer,
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### Database Schema

#### ingestion_jobs Table
Tracks ingestion jobs with status information:
- `id` (UUID): Unique job identifier
- `filename` (VARCHAR): Original filename
- `status` (VARCHAR): Job status (PENDING, PROCESSING, COMPLETED, FAILED)
- `variant_count` (INTEGER): Total variants ingested
- `created_at` (TIMESTAMP): Job creation time
- `updated_at` (TIMESTAMP): Last update time

#### variants Table
Stores parsed variant records:
- `id` (SERIAL): Record identifier
- `job_id` (UUID): Reference to ingestion job
- `chrom` (VARCHAR): Chromosome
- `pos` (INTEGER): Position
- `ref` (VARCHAR): Reference allele
- `alt` (VARCHAR): Alternate allele
- `qual` (FLOAT): Quality score
- `info` (TEXT): Additional information
- `created_at` (TIMESTAMP): Record creation time

### Kafka Event Schema

Events published to `raw_variants` topic:

```json
{
  "job_id": "uuid",
  "event_type": "raw_variants_ingested",
  "timestamp": "ISO8601",
  "variant_count": integer,
  "filename": "string",
  "status": "string",
  "errors": [],
  "file_hash": "sha256"
}
```

### Error Handling

- **400 Bad Request**: Invalid file format or validation failure
- **404 Not Found**: Job ID not found
- **500 Internal Server Error**: Database or processing errors

Error responses include:
- Error type
- Detailed message
- Optional list of specific issues encountered

### Deliverables to Other Dev Teams

- **Dev 4**: `src/schemas/variant_schema.sql` (Shared DB schema)
- **Dev 4**: `raw_variants_Kafka_topic_spec` (Orchestration layer)

### Testing

```bash
# Upload a VCF file
curl -X POST "http://localhost:8000/api/v1/ingestion/upload" \
  -F "file=@sample.vcf"

# Check job status
curl -X GET "http://localhost:8000/api/v1/ingestion/status/{job_id}"

# Health check
curl -X GET "http://localhost:8000/health"
```

### Future Enhancements

- FASTQ file parsing and processing
- BAM file parsing and processing
- Bulk file upload support
- Advanced variant filtering
- GraphQL API support
- Caching layer for frequently accessed data
- Performance optimization for large files

### Contributing

For development and feature requests, please create pull requests on the `dev1` branch.

### License

MIT