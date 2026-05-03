from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import logging
from typing import Optional

from src.api.schemas import IngestionResponse, JobStatusResponse, IngestionErrorResponse
from src.db.repository import VariantRepository
from src.parsers.vcf_parser import parse_vcf_file
from src.messaging.kafka_producer import get_producer
from src.storage.file_storage import FileStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])

file_storage = FileStorage()


@router.post("/upload", response_model=IngestionResponse)
async def upload_genomic_file(
    file: UploadFile = File(...),
    validate_only: bool = False
) -> IngestionResponse:
    """
    Upload and ingest genomic file (VCF, FASTQ, BAM).
    
    - Accepts file uploads in VCF, FASTQ, and BAM formats
    - Validates file format and integrity
    - Parses VCF files into structured variant records
    - Stores records in PostgreSQL
    - Publishes ingestion event to Kafka
    - Returns job ID for async tracking
    """
    job_id = None
    variant_count = 0
    errors = []
    
    try:
        # Create ingestion job
        job_id = VariantRepository.create_ingestion_job(file.filename)
        VariantRepository.update_job_status(job_id, 'PROCESSING')
        
        # Read and validate file content
        try:
            content = await file.read()
            
            # Validate file extension
            file_storage.validate_file_extension(file.filename)
            
            # Validate file integrity
            is_valid, file_hash = file_storage.validate_file_integrity(content)
            
            # Save file to storage
            file_path = file_storage.save_file(file.filename, content)
            logger.info(f"File stored at: {file_path}")
            
        except ValueError as e:
            error_msg = f"File validation failed: {str(e)}"
            logger.error(error_msg)
            errors.append(str(e))
            raise HTTPException(status_code=400, detail=error_msg)
        except Exception as e:
            error_msg = f"File processing error: {str(e)}"
            logger.error(error_msg)
            errors.append(str(e))
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Parse file based on extension
        if file.filename.lower().endswith('.vcf'):
            try:
                file_content_str = content.decode('utf-8')
                variants = parse_vcf_file(file_content_str)
                variant_count = len(variants)
                
                if not validate_only and variants:
                    # Store variants in database
                    VariantRepository.insert_variants(job_id, variants)
                
            except Exception as e:
                error_msg = f"VCF parsing failed: {str(e)}"
                logger.error(error_msg)
                errors.append(str(e))
                VariantRepository.update_job_status(job_id, 'FAILED')
                raise HTTPException(status_code=400, detail=error_msg)
        
        elif file.filename.lower().endswith('.fastq'):
            # FASTQ parsing placeholder
            logger.info("FASTQ files require separate processing pipeline")
            raise HTTPException(
                status_code=501,
                detail="FASTQ processing not yet implemented"
            )
        
        elif file.filename.lower().endswith('.bam'):
            # BAM parsing placeholder
            logger.info("BAM files require separate processing pipeline")
            raise HTTPException(
                status_code=501,
                detail="BAM processing not yet implemented"
            )
        
        # Update job status
        status = 'COMPLETED'
        VariantRepository.update_job_status(job_id, status, variant_count)
        
        # Publish event to Kafka
        try:
            producer = get_producer()
            event_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'variant_count': variant_count,
                'filename': file.filename,
                'status': status,
                'errors': errors,
                'file_hash': file_hash if 'file_hash' in locals() else None
            }
            producer.publish_ingestion_event(job_id, event_data)
        except Exception as e:
            logger.warning(f"Failed to publish Kafka event: {str(e)}")
            # Continue even if Kafka fails, as data is already stored
        
        return IngestionResponse(
            job_id=job_id,
            filename=file.filename,
            status=status,
            variant_count=variant_count,
            message=f"Successfully ingested {variant_count} variants"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error during ingestion: {str(e)}"
        logger.error(error_msg, exc_info=True)
        if job_id:
            VariantRepository.update_job_status(job_id, 'ERROR')
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_ingestion_status(job_id: str) -> JobStatusResponse:
    """Get the status of an ingestion job"""
    try:
        job = VariantRepository.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job not found: {job_id}"
            )
        
        return JobStatusResponse(
            job_id=job['id'],
            filename=job['filename'],
            status=job['status'],
            variant_count=job['variant_count'],
            created_at=job['created_at'].isoformat() if job['created_at'] else None,
            updated_at=job['updated_at'].isoformat() if job['updated_at'] else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
