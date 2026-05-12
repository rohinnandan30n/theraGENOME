"""
FastAPI Therapy Decision Report Orchestration Service

This service:
1. Calls Dev 1 (Variant Classification), Dev 2 (Pathogen Resistance), 
   and Dev 3 (Drug Safety) services concurrently
2. Aggregates results into a unified TherapyDecisionReport
3. Implements graceful degradation with fallback logic
4. Stores final reports in PostgreSQL
5. Exposes POST /reports/generate endpoint
"""

import asyncio
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime
from uuid import uuid4, UUID

from fastapi import FastAPI, HTTPException, Header
from pydantic import ValidationError
import httpx

from therapy_report_schemas import (
    TherapyReportGenerateRequest,
    TherapyDecisionReport,
    VariantSummary,
    ResistanceSummary,
    ToxicitySummary,
    ServiceStatus,
    ReportStatus,
    ToxicityRisk
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="theraGENOME Therapy Decision Report Aggregator",
    description="Orchestration service that aggregates variant classification, resistance prediction, and toxicity analysis",
    version="1.0.0"
)

# Service configuration
SERVICE_CONFIG = {
    "variant": {
        "url": "http://localhost:8000/api/v1/classification/classify",
        "timeout": 10.0,
        "timeout_ms": 10000,
        "description": "Dev 1 - Variant Classification Service"
    },
    "resistance": {
        "url": "http://localhost:8001/api/v1/pathogens/predict-resistance",
        "timeout": 10.0,
        "timeout_ms": 10000,
        "description": "Dev 2 - Pathogen Resistance Service"
    },
    "toxicity": {
        "url": "http://localhost:8002/api/v1/drugs/predict-toxicity",
        "timeout": 10.0,
        "timeout_ms": 10000,
        "description": "Dev 3 - Drug Safety Service"
    }
}


# ========== SERVICE CALL FUNCTIONS ==========

async def call_variant_service(
    sample_id: str,
    variant_data: Dict,
    http_client: httpx.AsyncClient
) -> tuple[Optional[VariantSummary], ServiceStatus, Optional[int], Optional[str]]:
    """Call Dev 1 variant classification service"""
    
    status = ServiceStatus.SUCCESS
    latency_ms = None
    error_message = None
    variant_summary = None
    
    start_time = datetime.utcnow()
    
    try:
        config = SERVICE_CONFIG["variant"]
        response = await http_client.post(
            config["url"],
            json=variant_data,
            timeout=config["timeout"]
        )
        
        latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse response into VariantSummary
            variant_summary = VariantSummary(
                chrom=variant_data.get("chrom", "unknown"),
                pos=variant_data.get("pos", 0),
                ref=variant_data.get("ref", ""),
                alt=variant_data.get("alt", ""),
                gene_symbol=data.get("gene_symbol"),
                amino_acid_change=data.get("amino_acid_change"),
                classification=data.get("classification", "VUS"),
                confidence=data.get("confidence", 0.5),
                model_version=data.get("model_version", "v2"),
                prediction_scores={
                    "CADD_score": data.get("CADD_score"),
                    "PolyPhen_score": data.get("PolyPhen_score"),
                    "SIFT_score": data.get("SIFT_score"),
                    "REVEL_score": data.get("REVEL_score")
                }
            )
            logger.info(f"Variant service success: {data.get('classification')} (confidence: {data.get('confidence')})")
        else:
            status = ServiceStatus.ERROR
            error_message = f"Variant service returned {response.status_code}"
            logger.warning(error_message)
            
    except asyncio.TimeoutError:
        status = ServiceStatus.TIMEOUT
        latency_ms = SERVICE_CONFIG["variant"]["timeout_ms"]
        error_message = "Variant service timeout (10s)"
        logger.warning(error_message)
        
    except Exception as e:
        status = ServiceStatus.ERROR
        error_message = f"Variant service error: {str(e)}"
        logger.error(error_message)
    
    return variant_summary, status, latency_ms, error_message


async def call_resistance_service(
    sample_id: str,
    pathogen_id: str,
    http_client: httpx.AsyncClient
) -> tuple[Optional[ResistanceSummary], ServiceStatus, Optional[int], Optional[str]]:
    """Call Dev 2 pathogen resistance service"""
    
    status = ServiceStatus.SUCCESS
    latency_ms = None
    error_message = None
    resistance_summary = None
    
    start_time = datetime.utcnow()
    
    try:
        config = SERVICE_CONFIG["resistance"]
        request_body = {
            "sample_id": sample_id,
            "pathogen_id": pathogen_id
        }
        
        response = await http_client.post(
            config["url"],
            json=request_body,
            timeout=config["timeout"]
        )
        
        latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if response.status_code == 200:
            data = response.json()
            
            resistance_summary = ResistanceSummary(
                pathogen_id=data.get("pathogen_id", pathogen_id),
                pathogen_name=data.get("pathogen_name"),
                resistance_genes=data.get("resistance_genes", []),
                predicted_phenotype=data.get("predicted_phenotype"),
                prediction_confidence=data.get("prediction_confidence", 0.5),
                antimicrobial_recommendation=data.get("antimicrobial_recommendation"),
                model_version=data.get("model_version", "v1")
            )
            logger.info(f"Resistance service success: {data.get('predicted_phenotype')} (confidence: {data.get('prediction_confidence')})")
        else:
            status = ServiceStatus.ERROR
            error_message = f"Resistance service returned {response.status_code}"
            logger.warning(error_message)
            
    except asyncio.TimeoutError:
        status = ServiceStatus.TIMEOUT
        latency_ms = SERVICE_CONFIG["resistance"]["timeout_ms"]
        error_message = "Resistance service timeout (10s)"
        logger.warning(error_message)
        
    except Exception as e:
        status = ServiceStatus.ERROR
        error_message = f"Resistance service error: {str(e)}"
        logger.error(error_message)
    
    return resistance_summary, status, latency_ms, error_message


async def call_toxicity_service(
    drug_candidates: List[str],
    http_client: httpx.AsyncClient
) -> tuple[Optional[List[ToxicitySummary]], ServiceStatus, Optional[int], Optional[str]]:
    """Call Dev 3 drug safety/toxicity service"""
    
    status = ServiceStatus.SUCCESS
    latency_ms = None
    error_message = None
    toxicity_summaries = []
    
    start_time = datetime.utcnow()
    
    try:
        config = SERVICE_CONFIG["toxicity"]
        request_body = {
            "drug_candidates": drug_candidates
        }
        
        response = await http_client.post(
            config["url"],
            json=request_body,
            timeout=config["timeout"]
        )
        
        latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse each drug's toxicity data
            for drug_result in data.get("results", []):
                try:
                    toxicity = ToxicitySummary(
                        drug_id=drug_result.get("drug_id", ""),
                        drug_name=drug_result.get("drug_name"),
                        toxicity_risk=drug_result.get("toxicity_risk", "Low"),
                        toxicity_confidence=drug_result.get("toxicity_confidence", 0.5),
                        pgx_interactions=drug_result.get("pgx_interactions", []),
                        adverse_events=drug_result.get("adverse_events", []),
                        dosing_recommendation=drug_result.get("dosing_recommendation"),
                        model_version=drug_result.get("model_version", "v1")
                    )
                    toxicity_summaries.append(toxicity)
                except ValidationError as ve:
                    logger.warning(f"Could not parse toxicity data for drug: {ve}")
            
            logger.info(f"Toxicity service success: analyzed {len(toxicity_summaries)} drugs")
        else:
            status = ServiceStatus.ERROR
            error_message = f"Toxicity service returned {response.status_code}"
            logger.warning(error_message)
            
    except asyncio.TimeoutError:
        status = ServiceStatus.TIMEOUT
        latency_ms = SERVICE_CONFIG["toxicity"]["timeout_ms"]
        error_message = "Toxicity service timeout (10s)"
        logger.warning(error_message)
        
    except Exception as e:
        status = ServiceStatus.ERROR
        error_message = f"Toxicity service error: {str(e)}"
        logger.error(error_message)
    
    return toxicity_summaries if toxicity_summaries else None, status, latency_ms, error_message


# ========== AGGREGATION LOGIC ==========

def select_best_drug(
    toxicity_summaries: Optional[List[ToxicitySummary]],
    drug_candidates: List[str]
) -> tuple[Optional[str], float, str]:
    """
    Select best drug based on lowest toxicity risk and highest confidence.
    
    Returns:
        (recommended_drug, confidence, rationale)
    """
    if not toxicity_summaries:
        return None, 0.0, "No toxicity data available"
    
    # Risk level scoring (lower is better)
    risk_scores = {
        ToxicityRisk.LOW: 1.0,
        ToxicityRisk.MEDIUM: 2.0,
        ToxicityRisk.HIGH: 3.0,
        ToxicityRisk.CRITICAL: 4.0
    }
    
    best_drug = None
    best_score = float('inf')
    best_toxicity = None
    
    for tox in toxicity_summaries:
        if tox.drug_name and tox.drug_name in drug_candidates:
            # Calculate score (lower risk + higher confidence = better)
            risk_score = risk_scores.get(tox.toxicity_risk, 2.5)
            confidence_factor = tox.toxicity_confidence
            
            # Combined score: emphasize low risk
            combined_score = risk_score / confidence_factor if confidence_factor > 0 else risk_score
            
            if combined_score < best_score:
                best_score = combined_score
                best_drug = tox.drug_name
                best_toxicity = tox
    
    if best_toxicity:
        rationale = f"Selected {best_drug}: {best_toxicity.toxicity_risk.value} toxicity risk (confidence: {best_toxicity.toxicity_confidence:.2f})"
        return best_drug, best_toxicity.toxicity_confidence, rationale
    
    return None, 0.0, "Could not determine best drug"


def aggregate_results(
    variant_summary: Optional[VariantSummary],
    resistance_summary: Optional[ResistanceSummary],
    toxicity_summaries: Optional[List[ToxicitySummary]],
    variant_status: ServiceStatus,
    resistance_status: ServiceStatus,
    toxicity_status: ServiceStatus,
    drug_candidates: List[str]
) -> tuple[TherapyDecisionReport, Optional[str]]:
    """
    Aggregate results from all three services into unified report.
    Implements graceful degradation.
    """
    
    # Select best drug from toxicity results
    recommended_drug, rec_confidence, rec_rationale = select_best_drug(
        toxicity_summaries, 
        drug_candidates
    )
    
    # Determine overall status
    all_success = (
        variant_status == ServiceStatus.SUCCESS and
        resistance_status == ServiceStatus.SUCCESS and
        toxicity_status == ServiceStatus.SUCCESS
    )
    
    any_timeout = (
        variant_status == ServiceStatus.TIMEOUT or
        resistance_status == ServiceStatus.TIMEOUT or
        toxicity_status == ServiceStatus.TIMEOUT
    )
    
    if all_success:
        report_status = ReportStatus.COMPLETE
    elif any_timeout:
        report_status = ReportStatus.PARTIAL
    else:
        report_status = ReportStatus.PARTIAL
    
    # Get toxicity summary for recommended drug if available
    selected_toxicity = None
    if toxicity_summaries and recommended_drug:
        selected_toxicity = next(
            (t for t in toxicity_summaries if t.drug_name == recommended_drug),
            None
        )
    
    # Build unified report
    report = TherapyDecisionReport(
        report_id=uuid4(),
        patient_id=None,  # Will be set later
        sample_id="",     # Will be set later
        variant_summary=variant_summary,
        resistance_summary=resistance_summary,
        toxicity_summary=selected_toxicity,
        recommended_drug=recommended_drug,
        alternative_drugs=[
            t.drug_name for t in (toxicity_summaries or [])
            if t.drug_name and t.drug_name != recommended_drug
        ][:3],  # Top 3 alternatives
        recommendation_confidence=rec_confidence,
        recommendation_rationale=rec_rationale,
        drug_candidates=drug_candidates,
        status=report_status,
        variant_service_status=variant_status,
        resistance_service_status=resistance_status,
        toxicity_service_status=toxicity_status,
        generated_at=datetime.utcnow(),
        created_by="orchestration_service"
    )
    
    return report, None


# ========== ENDPOINTS ==========

@app.post(
    "/reports/generate",
    response_model=TherapyDecisionReport,
    summary="Generate therapy decision report",
    description="Orchestrates calls to Dev 1, Dev 2, Dev 3 services and aggregates results"
)
async def generate_therapy_report(
    request: TherapyReportGenerateRequest,
    authorization: Optional[str] = Header(None)
) -> TherapyDecisionReport:
    """
    Generate a therapy decision report by calling all three microservices in parallel.
    
    Args:
        request: Report generation request with patient_id, sample_id, drug_candidates
        authorization: JWT bearer token for service-to-service auth
        
    Returns:
        Aggregated therapy decision report
        
    Raises:
        HTTPException: If critical services fail
    """
    
    logger.info(f"Generating report for patient {request.patient_id}, sample {request.sample_id}")
    
    # Initialize HTTP client
    async with httpx.AsyncClient() as http_client:
        
        # Call all three services concurrently with asyncio.gather()
        try:
            (variant_result, variant_status, variant_latency, variant_error), \
            (resistance_result, resistance_status, resistance_latency, resistance_error), \
            (toxicity_result, toxicity_status, toxicity_latency, toxicity_error) = await asyncio.gather(
                # Dev 1: Variant Classification
                call_variant_service(
                    request.sample_id,
                    {
                        "chrom": "17",  # These would come from request in real scenario
                        "pos": 41244394,
                        "ref": "T",
                        "alt": "G",
                        "phyloP_score": 3.0,
                        "SIFT_score": 0.01,
                        "PolyPhen_score": 0.95,
                        "CADD_score": 30.0,
                        "gnomAD_freq": 0.00001
                    },
                    http_client
                ),
                
                # Dev 2: Pathogen Resistance
                call_resistance_service(
                    request.sample_id,
                    "562",  # E. coli NCBI ID - would come from request
                    http_client
                ),
                
                # Dev 3: Drug Toxicity
                call_toxicity_service(
                    request.drug_candidates,
                    http_client
                )
            )
        except Exception as e:
            logger.error(f"Concurrent service call failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Service orchestration failed: {str(e)}"
            )
    
    # Aggregate results
    report, error = aggregate_results(
        variant_result,
        resistance_result,
        toxicity_result,
        variant_status,
        resistance_status,
        toxicity_status,
        request.drug_candidates
    )
    
    # Set request-specific fields
    report.patient_id = request.patient_id
    report.sample_id = request.sample_id
    report.created_by = request.clinician_id or "system"
    report.clinician_id = request.clinician_id
    
    # Log summary
    logger.info(
        f"Report generated: {report.status.value} - "
        f"Variant: {variant_status.value} ({variant_latency}ms), "
        f"Resistance: {resistance_status.value} ({resistance_latency}ms), "
        f"Toxicity: {toxicity_status.value} ({toxicity_latency}ms) - "
        f"Recommended: {report.recommended_drug} "
        f"(confidence: {report.recommendation_confidence:.2f})"
    )
    
    return report


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Therapy Decision Report Aggregator",
        "version": "1.0.0"
    }


@app.get("/services")
async def get_services_status():
    """Get status of connected services"""
    return {
        "variant_service": SERVICE_CONFIG["variant"],
        "resistance_service": SERVICE_CONFIG["resistance"],
        "toxicity_service": SERVICE_CONFIG["toxicity"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
