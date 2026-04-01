"""FastAPI service for multi-omics data ingestion and processing."""

import os
import time
import tempfile
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Local imports
from omics_schemas import (
    OmicsUploadRequest, 
    RNAResult,
    ProteinResult,
    OmicsIntegrationEvent,
    ToxicityGuardIntegration
)
from rna_processor import RNASeqProcessor
from proteomics_processor import ProteomicsProcessor
from omics_repository import OmicsRepository
from omics_kafka_publisher import OmicsKafkaPublisher


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ==================== CONFIGURATION ====================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/theragenome"
)
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")

# ==================== DATABASE SETUP ====================

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        yield session


# ==================== KAFKA SETUP ====================

kafka_publisher = OmicsKafkaPublisher(bootstrap_servers=KAFKA_BROKERS)


# ==================== FASTAPI APP ====================

app = FastAPI(
    title="TheraGenome Omics Ingestion Pipeline",
    description="RNA-seq and proteomics data processing service",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        await kafka_publisher.start()
        logger.info("Omics service started successfully")
    except Exception as e:
        logger.warning(f"Kafka not available: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await kafka_publisher.stop()
    logger.info("Omics service shut down")


# ==================== HEALTH ENDPOINTS ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "omics_pipeline"}


@app.get("/status")
async def status():
    """Service status endpoint."""
    return {
        "status": "running",
        "service": "omics_pipeline",
        "version": "1.0.0",
        "database_url": DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else "configured",
        "kafka_brokers": KAFKA_BROKERS,
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== RNA-SEQ ENDPOINTS ====================

@app.post("/omics/rna-seq/process")
async def process_rna_seq(
    patient_id: str,
    file: UploadFile = File(...),
    case_samples: Optional[str] = None,
    control_samples: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    session: AsyncSession = Depends(get_session)
):
    """
    Upload and process RNA-seq count matrix (CSV or H5AD format).

    Args:
        patient_id: Patient UUID
        file: Count matrix file (CSV or H5AD)
        case_samples: Comma-separated case sample names
        control_samples: Comma-separated control sample names
        background_tasks: Background task runner
        session: Database session

    Returns:
        Processing job result
    """
    try:
        patient_uuid = UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient_id format")

    # Validate samples
    if not case_samples or not control_samples:
        raise HTTPException(status_code=400, detail="case_samples and control_samples required")

    case_list = [s.strip() for s in case_samples.split(",")]
    control_list = [s.strip() for s in control_samples.split(",")]

    # Save uploaded file to temp location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv" if file.filename.endswith(".csv") else ".h5ad") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        logger.info(f"Processing RNA-seq for patient {patient_id}: {file.filename}")

        # Process in background
        background_tasks.add_task(
            _process_rna_seq_background,
            patient_uuid,
            tmp_path,
            case_list,
            control_list,
            session
        )

        return {
            "status": "processing",
            "patient_id": str(patient_uuid),
            "data_type": "rna-seq",
            "file": file.filename,
            "message": "RNA-seq processing started in background"
        }

    except Exception as e:
        logger.error(f"Error processing RNA-seq: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


async def _process_rna_seq_background(
    patient_id: UUID,
    file_path: str,
    case_samples: list,
    control_samples: list,
    session: AsyncSession
):
    """Background task for RNA-seq processing."""
    start_time = time.time()
    repo = OmicsRepository(session)

    try:
        # Process RNA-seq data
        de_results, metadata = RNASeqProcessor.process_rna_seq(
            file_path,
            case_samples,
            control_samples
        )

        # Prepare database records
        rna_records = []
        for gene_id, row in de_results.iterrows():
            rna_records.append({
                'patient_id': patient_id,
                'gene_id': gene_id,
                'gene_name': row.get('gene_name', gene_id),
                'log2_fold_change': float(row['log2_fold_change']),
                'p_value': float(row['p_value']),
                'padj': float(row['padj']),
                'base_mean': float(row.get('base_mean', 0)),
                'case_mean': float(row.get('case_mean', 0)),
                'control_mean': float(row.get('control_mean', 0)),
                'significance_flag': row.get('significance_flag'),
                'effect_size': float(row.get('effect_size', 0)),
                'expression_level': row.get('expression_level'),
                'transcript_biotype': row.get('transcript_biotype'),
                'metadata': metadata
            })

        # Store in database
        record_count = await repo.create_rna_results(rna_records)
        await session.commit()

        # Publish event
        processing_duration = time.time() - start_time
        await kafka_publisher.publish_rna_processed(
            patient_id=patient_id,
            record_count=record_count,
            processing_duration=processing_duration,
            significant_genes=metadata.get('significant_genes', 0),
            upregulated=metadata.get('upregulated_genes', 0),
            downregulated=metadata.get('downregulated_genes', 0)
        )

        logger.info(f"RNA-seq processing complete for {patient_id}: {record_count} genes, {processing_duration:.1f}s")

    except Exception as e:
        logger.error(f"Background RNA-seq processing error: {e}")
        await kafka_publisher.publish_omics_error(
            patient_id=patient_id,
            data_type="rna-seq",
            error_message=str(e),
            file_path=file_path
        )
    finally:
        # Cleanup temp file
        if os.path.exists(file_path):
            os.unlink(file_path)


# ==================== PROTEOMICS ENDPOINTS ====================

@app.post("/omics/proteomics/process")
async def process_proteomics(
    patient_id: str,
    file: UploadFile = File(...),
    case_samples: Optional[str] = None,
    control_samples: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    session: AsyncSession = Depends(get_session)
):
    """
    Upload and process proteomics data (MaxQuant proteinGroups.txt).

    Args:
        patient_id: Patient UUID
        file: MaxQuant output TSV file
        case_samples: Optional comma-separated case samples
        control_samples: Optional comma-separated control samples
        background_tasks: Background task runner
        session: Database session

    Returns:
        Processing job result
    """
    try:
        patient_uuid = UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient_id format")

    case_list = [s.strip() for s in case_samples.split(",")] if case_samples else None
    control_list = [s.strip() for s in control_samples.split(",")] if control_samples else None

    # Save uploaded file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        logger.info(f"Processing proteomics for patient {patient_id}: {file.filename}")

        # Process in background
        background_tasks.add_task(
            _process_proteomics_background,
            patient_uuid,
            tmp_path,
            case_list,
            control_list,
            session
        )

        return {
            "status": "processing",
            "patient_id": str(patient_uuid),
            "data_type": "proteomics",
            "file": file.filename,
            "message": "Proteomics processing started in background"
        }

    except Exception as e:
        logger.error(f"Error processing proteomics: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


async def _process_proteomics_background(
    patient_id: UUID,
    file_path: str,
    case_samples: Optional[list],
    control_samples: Optional[list],
    session: AsyncSession
):
    """Background task for proteomics processing."""
    start_time = time.time()
    repo = OmicsRepository(session)

    try:
        # Process proteomics data
        results, metadata = ProteomicsProcessor.process_proteomics(
            file_path,
            case_samples,
            control_samples
        )

        # Prepare database records
        protein_records = []
        for idx, row in results.iterrows():
            protein_records.append({
                'patient_id': patient_id,
                'protein_id': row.get('protein_id', f"protein_{idx}"),
                'protein_name': row.get('protein_name', 'Unknown'),
                'gene_name': row.get('gene_name'),
                'uniprot_id': row.get('uniprot_id'),
                'lfq_intensity': float(row.get('lfq_intensity', 0)),
                'log2_intensity': float(row.get('log2_intensity', 0)),
                'peptide_count': int(row.get('peptide_count', 0)) if pd.notna(row.get('peptide_count')) else None,
                'unique_peptides': int(row.get('unique_peptides', 0)) if pd.notna(row.get('unique_peptides')) else None,
                'protein_class': row.get('protein_class'),
                'sequence_coverage': float(row.get('sequence_coverage', 0)) if pd.notna(row.get('sequence_coverage')) else None,
                'molecular_weight': float(row.get('molecular_weight', 0)) if pd.notna(row.get('molecular_weight')) else None,
                'metadata': metadata
            })

        # Store in database
        record_count = await repo.create_protein_results(protein_records)
        await session.commit()

        # Publish event
        processing_duration = time.time() - start_time
        await kafka_publisher.publish_proteomics_processed(
            patient_id=patient_id,
            record_count=record_count,
            processing_duration=processing_duration,
            detected_proteins=metadata.get('total_proteins_quantified', 0),
            drug_targets=metadata.get('drug_target_proteins', 0),
            enzymes=metadata.get('enzyme_proteins', 0)
        )

        logger.info(f"Proteomics processing complete for {patient_id}: {record_count} proteins, {processing_duration:.1f}s")

    except Exception as e:
        logger.error(f"Background proteomics processing error: {e}")
        await kafka_publisher.publish_omics_error(
            patient_id=patient_id,
            data_type="proteomics",
            error_message=str(e),
            file_path=file_path
        )
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)


# ==================== QUERY ENDPOINTS ====================

@app.get("/omics/patients/{patient_id}/rna")
async def get_patient_rna(patient_id: str, session: AsyncSession = Depends(get_session)):
    """Get RNA-seq results for a patient."""
    try:
        patient_uuid = UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient_id")

    repo = OmicsRepository(session)
    results = await repo.get_rna_results_by_patient(patient_uuid, limit=100)

    return {
        "patient_id": patient_id,
        "data_type": "rna-seq",
        "result_count": len(results),
        "results": [
            {
                "gene_id": r.gene_id,
                "gene_name": r.gene_name,
                "log2_fold_change": r.log2_fold_change,
                "padj": r.padj,
                "significance_flag": r.significance_flag
            }
            for r in results
        ]
    }


@app.get("/omics/patients/{patient_id}/proteins")
async def get_patient_proteins(patient_id: str, session: AsyncSession = Depends(get_session)):
    """Get proteomics results for a patient."""
    try:
        patient_uuid = UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient_id")

    repo = OmicsRepository(session)
    results = await repo.get_protein_results_by_patient(patient_uuid, limit=100)

    return {
        "patient_id": patient_id,
        "data_type": "proteomics",
        "result_count": len(results),
        "results": [
            {
                "protein_id": r.protein_id,
                "protein_name": r.protein_name,
                "gene_name": r.gene_name,
                "log2_intensity": r.log2_intensity,
                "protein_class": r.protein_class
            }
            for r in results
        ]
    }


@app.get("/omics/stats")
async def get_statistics(session: AsyncSession = Depends(get_session)):
    """Get omics ingestion statistics."""
    repo = OmicsRepository(session)

    rna_count = await repo.count_rna_results()
    protein_count = await repo.count_protein_results()
    rna_patients = await repo.count_patients_with_rna()
    proteomics_patients = await repo.count_patients_with_proteomics()

    return {
        "total_rna_results": rna_count,
        "total_protein_results": protein_count,
        "patients_with_rna": rna_patients,
        "patients_with_proteomics": proteomics_patients,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
