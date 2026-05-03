# Task 1.2 - Variant Database Integration Implementation

## Overview
This document describes the implementation of Task 1.2: Variant Database Integration (ClinVar / gnomAD / HGMD)

## Components Implemented

### 1. ClinVar Integration (`src/external_apis/clinvar.py`)
- **ClinVarDownloader**: Downloads and parses latest ClinVar XML dumps
- Features:
  - Automated download from NCBI FTP
  - Automatic decompression of gzipped files
  - Batch parsing to handle large files efficiently
  - XML parsing with streaming to minimize memory usage
  - Extracts: variation_id, gene_symbol, HGVS expression, clinical significance, review status

**Methods:**
- `download_clinvar_dump()`: Download latest ClinVar XML dump from FTP
- `decompress_gzip()`: Decompress gzipped ClinVar file
- `parse_clinvar_xml()`: Stream-parse XML and yield variant batches
- `_extract_variant_record()`: Extract individual variant data from XML

### 2. gnomAD API Integration (`src/external_apis/gnomad.py`)
- **GnomADAPI**: Integration with gnomAD GraphQL API
- Features:
  - GraphQL query templates for variant and population queries
  - Retrieves allele frequencies (exome and genome)
  - Population-specific frequency data
  - Error handling and logging

**Methods:**
- `query_variant_frequency()`: Query variant allele frequencies
- `query_population_frequencies()`: Get population-specific frequencies
- `parse_variant_id()`: Convert coordinates to gnomAD format (chrom-pos-ref-alt)
- `parse_variant_coordinates()`: Parse gnomAD variant ID to coordinates

### 3. Redis Caching Layer (`src/cache/redis_cache.py`)
- **RedisCache**: High-performance caching with TTL support
- Features:
  - JSON serialization for complex objects
  - 24-hour default TTL (configurable)
  - Pattern-based cache invalidation
  - Connection pooling

**Methods:**
- `get()`: Retrieve cached value
- `set()`: Store value with TTL
- `delete()`: Remove cached entry
- `clear_pattern()`: Clear all matching pattern keys
- `close()`: Close Redis connection

### 4. Database Integration (`src/db/variant_repository.py`)
Three repository classes for data access:

#### ClinVarRepository
- `upsert_clinvar_variant()`: Insert/update single variant
- `batch_upsert_clinvar_variants()`: Batch insert/update variants
- `get_clinvar_by_variation_id()`: Lookup by variation ID
- `get_clinvar_by_hgvs()`: Lookup by HGVS expression
- `get_clinvar_by_gene()`: Get all variants for a gene

#### GnomADRepository
- `upsert_gnomad_frequency()`: Insert/update frequency data
- `get_gnomad_by_variant_id()`: Lookup by variant ID
- `get_gnomad_by_coordinates()`: Lookup by genomic coordinates

#### EnrichedVariantRepository
- `create_enriched_variant()`: Create combined ClinVar + gnomAD record
- `get_enriched_variant()`: Retrieve enriched variant data
- JSON serialization for complex metadata

### 5. REST API Endpoints (`src/api/variants.py`)

#### GET /api/v1/variants/{rsid}
Retrieve enriched variant data combining ClinVar and gnomAD

**Query Parameters:**
- `include_gnomad` (bool): Include gnomAD data (default: true)
- `use_cache` (bool): Use cached results (default: true)

**Response:**
```json
{
  "variant_id": "12345",
  "clinvar_data": {
    "variation_id": "12345",
    "rcv_id": "RCV000000001",
    "gene_symbol": "BRCA1",
    "hgvs_expression": "NC_000017.11:g.41244394T>G",
    "clinical_significance": "Pathogenic",
    "review_status": "4"
  },
  "gnomad_data": {
    "variant_id": "17-41244394-T-G",
    "chrom": "17",
    "pos": 41244394,
    "ref": "T",
    "alt": "G",
    "genome_af": 0.0000567,
    "exome_af": 0.0001234
  },
  "allele_frequency": 0.0000567,
  "clinical_significance": "Pathogenic",
  "enriched_metadata": {
    "last_updated": "2024-03-30T12:00:00Z",
    "data_sources": ["ClinVar", "gnomAD"]
  }
}
```

#### GET /api/v1/variants/frequency/{chrom}/{pos}/{ref}/{alt}
Get allele frequency for specific genomic coordinates

**Response:**
```json
{
  "variant_id": "17-41244394-T-G",
  "chrom": "17",
  "pos": 41244394,
  "ref": "T",
  "alt": "G",
  "exome_af": 0.0001234,
  "genome_af": 0.0000567,
  "exome_ac": 15,
  "exome_an": 121656,
  "genome_ac": 7,
  "genome_an": 123136
}
```

### 6. Database Schema (`src/schemas/variant_integration_schema.sql`)

#### clinvar_variants Table
- `variation_id` (VARCHAR UNIQUE): ClinVar variation identifier
- `rcv_id` (VARCHAR UNIQUE): RCV accession
- `gene_symbol` (VARCHAR): HGNC gene symbol
- `hgvs_expression` (VARCHAR UNIQUE): HGVS nomenclature
- `variant_type` (VARCHAR): Type (Substitution, Deletion, etc.)
- `ref_allele` (VARCHAR): Reference allele
- `alt_allele` (VARCHAR): Alternate allele
- `clinical_significance` (VARCHAR): Clinical class
- `review_status` (VARCHAR): ClinVar review score
- Indexes on: variation_id, rcv_id, hgvs_expression, gene_symbol

#### gnomad_frequencies Table
- `variant_id` (VARCHAR UNIQUE): gnomAD variant ID
- `chrom`, `pos`, `ref`, `alt`: Genomic coordinates
- `exome_ac`, `exome_an`, `exome_af`: Exome frequencies
- `genome_ac`, `genome_an`, `genome_af`: Genome frequencies
- Foreign key to clinvar_variants
- Indexes on: variant_id, chrom-pos

#### enriched_variants Table
- `variant_id` (VARCHAR UNIQUE): Primary variant identifier
- `clinvar_data` (JSON): Full ClinVar record
- `gnomad_data` (JSON): Full gnomAD record
- `hgvs_mapping` (VARCHAR): HGVS expression
- `enriched_metadata` (JSON): Additional metadata
- Indexes on: variant_id

### 7. Sync Scripts

#### sync_clinvar.py (`scripts/sync_clinvar.py`)
Automated ClinVar database synchronization

**Features:**
- Downloads latest ClinVar XML dump from NCBI FTP
- Decompresses gzipped archive
- Batch parses and upserts variants
- Progress tracking with ETA
- Optional file cleanup after sync

**Usage:**
```bash
python scripts/sync_clinvar.py --batch-size 1000 --keep-files
```

#### init_db.py (`scripts/init_db.py`)
Initialize database schema

**Usage:**
```bash
python scripts/init_db.py
```

## Configuration

Update `.env` with:
```env
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_CACHE_TTL_HOURS=24

# External APIs
GNOMAD_TIMEOUT=10
CLINVAR_DOWNLOAD_PATH=./data/clinvar
```

## Data Flow

1. **Ingestion**: Incoming variants from Task 1.1
   ↓
2. **ClinVar Enrichment**: Look up in ClinVar database
   ↓
3. **gnomAD Enrichment**: Query gnomAD for population frequencies
   ↓
4. **Caching**: Store in Redis (24-hour TTL)
   ↓
5. **Database Storage**: Persist enriched variant in enriched_variants table
   ↓
6. **API Response**: Return combined ClinVar + gnomAD data

## Performance Optimizations

1. **Redis Caching**: 24-hour TTL reduces database queries
2. **Database Indexing**: Optimized indexes for fast lookups
3. **Lazy Loading**: gnomAD data fetched on-demand
4. **Batch Operations**: Efficient bulk inserts for ClinVar sync
5. **Connection Pooling**: Reused database connections

## Testing

### Test ClinVar Sync
```bash
python scripts/sync_clinvar.py --batch-size 100
```

### Test Variant Lookup
```bash
curl "http://localhost:8000/api/v1/variants/12345"
```

### Test Allele Frequency Lookup
```bash
curl "http://localhost:8000/api/v1/variants/frequency/17/41244394/T/G"
```

## Deliverables to Dev 4

- **OpenAPI Specification**: [docs/variant_api.openapi.yaml](../docs/variant_api.openapi.yaml)
  - Full REST API contract for variant endpoints
  - Includes request/response schemas
  - Error response definitions

## Future Enhancements

1. **HGMD Integration**: Add HGMD (Human Gene Mutation Database) data
2. **Population Filtering**: Advanced population-level filtering
3. **Batch Queries**: Support bulk variant lookups
4. **Export Formats**: VCF, JSON export capabilities
5. **Performance Analytics**: Cache hit rates, query times
6. **GraphQL API**: Alternative GraphQL interface
7. **Variant Classification**: ML-based pathogenicity prediction

## Dependencies

- `requests`: HTTP client for gnomAD GraphQL API
- `redis`: Redis client for caching
- `psycopg2-binary`: PostgreSQL database adapter
- All existing dependencies from Task 1.1

## Error Handling

- **404 Not Found**: Variant not in database
- **500 Server Error**: Database or API failures
- Graceful fallback when gnomAD unavailable
- Detailed error logging for debugging

## Deployment Notes

1. Launch Redis server before application
2. Initialize database schema: `python scripts/init_db.py`
3. Optionally sync ClinVar: `python scripts/sync_clinvar.py`
4. Start application: `python -m src.main`

The API is production-ready with comprehensive error handling, caching, and monitoring.
