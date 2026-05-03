"""
Smart Reporter Service (Task 4.5)

FastAPI endpoint that:
- Fetches TherapyDecisionReport JSON
- Retrieves SHAP explanations from Dev 1, 2, 3
- Calls LLM with structured prompts
- Streams narrative response via Server-Sent Events (SSE)
- Stores narrative in database
"""

import asyncio
import time
from typing import Optional, AsyncGenerator
from datetime import datetime
from uuid import UUID
import json
import logging

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from scripts.therapy_report_repository import TherapyReportRepository
from scripts.therapy_report_schemas import TherapyDecisionReport
from scripts.narrative_repository import NarrativeReportRepository, NarrativeReport
from scripts.shap_schemas import (
    VariantSHAPExplanation,
    ResistanceSHAPExplanation,
    ToxicitySHAPExplanation,
    UnifiedXAIExplanation
)
from scripts.llm_narrative_service import MedicalLLMService, LLMConfig
from scripts.db_connection import get_async_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Reporter (Task 4.5) - Medical LLM Integration",
    description="Narrative clinical report generation with SHAP explanations",
    version="1.0.0"
)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

from pydantic import BaseModel, Field


class NarrativeGenerationRequest(BaseModel):
    """Request to generate narrative for a therapy report."""
    therapy_report_id: str = Field(..., description="Therapy report ID")
    include_shap_explanations: bool = Field(
        True,
        description="Include SHAP-based XAI explanations"
    )
    clinician_id: Optional[str] = Field(
        None,
        description="Clinician requesting narrative"
    )
    llm_temperature: float = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature for generation"
    )


class NarrativeResponse(BaseModel):
    """Response containing generated narrative."""
    narrative_id: str
    therapy_report_id: str
    patient_id: str
    narrative_text: str
    llm_model_used: str
    generation_duration_seconds: Optional[float]
    quality_scores: Optional[dict] = None
    generated_at: str


class NarrativeMetadata(BaseModel):
    """Metadata about a narrative."""
    narrative_id: str
    therapy_report_id: str
    patient_id: str
    llm_model_used: str
    readability_score: Optional[float]
    completeness_score: Optional[float]
    created_at: str
    clinician_id: Optional[str]


class ServiceStatsResponse(BaseModel):
    """Service statistics."""
    total_narratives_generated: int
    avg_generation_seconds: float
    avg_readability_score: Optional[float]
    avg_completeness_score: Optional[float]
    llm_models_used: dict


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_db() -> AsyncSession:
    """Get database session."""
    async for session in get_async_db():
        yield session


async def get_llm_service() -> MedicalLLMService:
    """Get LLM service."""
    service = MedicalLLMService(LLMConfig())
    try:
        yield service
    finally:
        await service.close()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def fetch_shap_explanations(
    therapy_report_id: str,
    include_shap: bool = True
) -> tuple[Optional[VariantSHAPExplanation], Optional[ResistanceSHAPExplanation], Optional[ToxicitySHAPExplanation]]:
    """
    Fetch SHAP explanations from Dev 1, 2, Dev 3.
    
    Returns: (variant_shap, resistance_shap, toxicity_shap)
    """
    
    if not include_shap:
        return None, None, None
    
    # In production, these would be fetched from:
    # - Dev 1 service: GET /explanations/variant/{therapy_report_id}
    # - Dev 2 service: GET /explanations/resistance/{therapy_report_id}
    # - Dev 3 service: GET /explanations/toxicity/{therapy_report_id}
    
    # For now, return mock SHAP objects
    # This would be replaced with actual HTTP calls
    
    return None, None, None


def parse_narrative_sections(narrative_text: str) -> dict:
    """Parse narrative into structured sections."""
    
    sections = {
        "patient_summary": "",
        "genetic_risk_analysis": "",
        "infection_resistance_profile": "",
        "drug_safety_assessment": "",
        "final_recommendation": "",
        "clinical_monitoring_plan": "",
        "limitations_caveats": ""
    }
    
    section_markers = {
        "patient_summary": ["PATIENT SUMMARY", "Patient Summary"],
        "genetic_risk_analysis": ["GENETIC RISK ANALYSIS", "Genetic Risk"],
        "infection_resistance_profile": ["INFECTION & RESISTANCE", "Resistance Profile"],
        "drug_safety_assessment": ["DRUG SAFETY", "Safety Assessment", "Toxicity"],
        "final_recommendation": ["FINAL RECOMMENDATION", "Recommendation"],
        "clinical_monitoring_plan": ["MONITORING PLAN", "Monitoring", "Follow-up"],
        "limitations_caveats": ["LIMITATIONS", "CAVEATS", "Limitations & Caveats"]
    }
    
    lines = narrative_text.split('\n')
    current_section = None
    
    for line in lines:
        # Check if this line starts a new section
        for section_name, markers in section_markers.items():
            if any(marker in line for marker in markers):
                current_section = section_name
                break
        
        # Add to current section
        if current_section:
            sections[current_section] += line + "\n"
    
    # Clean up sections
    for key in sections:
        sections[key] = sections[key].strip()
    
    return sections


async def stream_narrative_sse(
    narrative_stream: AsyncGenerator[str, None]
) -> AsyncGenerator[str, None]:
    """Convert narrative stream to Server-Sent Events format."""
    
    buffer = ""
    chunk_size = 50  # Emit every 50 characters
    
    async for chunk in narrative_stream:
        buffer += chunk
        
        # Emit chunk when buffer reaches size
        if len(buffer) >= chunk_size:
            # Escape for JSON
            escaped = json.dumps(buffer)
            yield f"data: {escaped}\n\n"
            buffer = ""
    
    # Emit remaining buffer
    if buffer:
        escaped = json.dumps(buffer)
        yield f"data: {escaped}\n\n"
    
    # Send completion signal
    yield 'data: {"status": "complete"}\n\n'


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Smart Reporter (Task 4.5)",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post(
    "/reports/{therapy_report_id}/narrative",
    response_class=StreamingResponse,
    tags=["Narrative Generation"]
)
async def generate_narrative_stream(
    therapy_report_id: str,
    request: NarrativeGenerationRequest,
    db: AsyncSession = Depends(get_db),
    llm_service: MedicalLLMService = Depends(get_llm_service)
):
    """
    Generate narrative clinical report with streaming (SSE).
    
    Streams the narrative text in real-time using Server-Sent Events.
    """
    
    start_time = time.time()
    
    try:
        # Fetch therapy report
        therapy_repo = TherapyReportRepository(db)
        therapy_report_data = await therapy_repo.get_by_id(therapy_report_id)
        
        if not therapy_report_data:
            raise HTTPException(status_code=404, detail="Therapy report not found")
        
        # Convert to Pydantic model
        therapy_report = TherapyDecisionReport(**therapy_report_data)
        
        # Fetch SHAP explanations
        variant_shap, resistance_shap, toxicity_shap = await fetch_shap_explanations(
            therapy_report_id,
            request.include_shap_explanations
        )
        
        # Configure LLM service
        llm_service.config.temperature = request.llm_temperature
        
        # Generate narrative with streaming
        async def generate_and_store():
            narrative_text = ""
            
            # Stream narrative
            async for chunk in llm_service.generate_narrative_stream(
                therapy_report,
                variant_shap,
                resistance_shap,
                toxicity_shap
            ):
                narrative_text += chunk
                # Send chunk via SSE
                escaped = json.dumps(chunk)
                yield f"data: {escaped}\n\n"
            
            # Store narrative in database
            elapsed_time = time.time() - start_time
            
            narrative_repo = NarrativeReportRepository(db)
            
            # Parse sections
            sections = parse_narrative_sections(narrative_text)
            
            # Create SHAP JSON objects (if available)
            variant_shap_json = variant_shap.dict() if variant_shap else None
            resistance_shap_json = resistance_shap.dict() if resistance_shap else None
            toxicity_shap_json = toxicity_shap.dict() if toxicity_shap else None
            
            await narrative_repo.create(
                therapy_report_id=therapy_report_id,
                patient_id=str(therapy_report.patient_id),
                narrative_text=narrative_text,
                narrative_sections=sections,
                llm_model_used=llm_service.config.openai_model or llm_service.config.ollama_model,
                variant_shap_json=variant_shap_json,
                resistance_shap_json=resistance_shap_json,
                toxicity_shap_json=toxicity_shap_json,
                generation_duration_seconds=elapsed_time,
                generation_temperature=request.llm_temperature,
                clinician_id=request.clinician_id,
                created_by=request.clinician_id
            )
            
            # Send completion signal
            yield f'data: {{"status": "complete", "duration_seconds": {elapsed_time:.2f}}}\n\n'
        
        return StreamingResponse(
            generate_and_store(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating narrative: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/reports/{therapy_report_id}/narrative/full",
    response_model=NarrativeResponse,
    tags=["Narrative Generation"]
)
async def generate_narrative_full(
    therapy_report_id: str,
    request: NarrativeGenerationRequest,
    db: AsyncSession = Depends(get_db),
    llm_service: MedicalLLMService = Depends(get_llm_service)
):
    """
    Generate narrative clinical report (full response, non-streaming).
    
    Returns complete narrative in single response.
    """
    
    start_time = time.time()
    
    try:
        # Fetch therapy report
        therapy_repo = TherapyReportRepository(db)
        therapy_report_data = await therapy_repo.get_by_id(therapy_report_id)
        
        if not therapy_report_data:
            raise HTTPException(status_code=404, detail="Therapy report not found")
        
        therapy_report = TherapyDecisionReport(**therapy_report_data)
        
        # Fetch SHAP explanations
        variant_shap, resistance_shap, toxicity_shap = await fetch_shap_explanations(
            therapy_report_id,
            request.include_shap_explanations
        )
        
        llm_service.config.temperature = request.llm_temperature
        
        # Generate narrative
        narrative_text = await llm_service.generate_narrative_full(
            therapy_report,
            variant_shap,
            resistance_shap,
            toxicity_shap
        )
        
        elapsed_time = time.time() - start_time
        
        # Store in database
        narrative_repo = NarrativeReportRepository(db)
        sections = parse_narrative_sections(narrative_text)
        
        narrative_dict = await narrative_repo.create(
            therapy_report_id=therapy_report_id,
            patient_id=str(therapy_report.patient_id),
            narrative_text=narrative_text,
            narrative_sections=sections,
            llm_model_used=llm_service.config.openai_model or llm_service.config.ollama_model,
            generation_duration_seconds=elapsed_time,
            generation_temperature=request.llm_temperature,
            clinician_id=request.clinician_id,
            created_by=request.clinician_id
        )
        
        await db.commit()
        
        return NarrativeResponse(
            narrative_id=narrative_dict["id"],
            therapy_report_id=narrative_dict["therapy_report_id"],
            patient_id=narrative_dict["patient_id"],
            narrative_text=narrative_text,
            llm_model_used=llm_service.config.openai_model or llm_service.config.ollama_model,
            generation_duration_seconds=elapsed_time,
            generated_at=narrative_dict["created_at"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating narrative: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/narratives/{narrative_id}",
    response_model=NarrativeResponse,
    tags=["Narratives"]
)
async def get_narrative(
    narrative_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve stored narrative report."""
    
    narrative_repo = NarrativeReportRepository(db)
    narrative = await narrative_repo.get_by_id(narrative_id)
    
    if not narrative:
        raise HTTPException(status_code=404, detail="Narrative not found")
    
    return NarrativeResponse(
        narrative_id=narrative["id"],
        therapy_report_id=narrative["therapy_report_id"],
        patient_id=narrative["patient_id"],
        narrative_text=narrative["narrative_text"],
        llm_model_used=narrative["llm_model_used"],
        generation_duration_seconds=narrative["generation_duration_seconds"],
        quality_scores={
            "readability": narrative["readability_score"],
            "terminology": narrative["medical_terminology_score"],
            "completeness": narrative["completeness_score"]
        },
        generated_at=narrative["created_at"]
    )


@app.get(
    "/patients/{patient_id}/narratives",
    tags=["Narratives"]
)
async def list_patient_narratives(
    patient_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List all narratives for a patient."""
    
    narrative_repo = NarrativeReportRepository(db)
    narratives, total = await narrative_repo.list_for_patient(patient_id, limit, offset)
    
    return {
        "patient_id": patient_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "narratives": narratives
    }


@app.get(
    "/stats",
    response_model=ServiceStatsResponse,
    tags=["Statistics"]
)
async def get_statistics(
    db: AsyncSession = Depends(get_db)
):
    """Get service statistics."""
    
    narrative_repo = NarrativeReportRepository(db)
    stats = await narrative_repo.get_statistics()
    
    return ServiceStatsResponse(
        total_narratives_generated=stats["total_narratives"],
        avg_generation_seconds=stats["avg_generation_seconds"],
        avg_readability_score=stats["avg_readability_score"],
        avg_completeness_score=stats["avg_completeness_score"],
        llm_models_used=stats["models_used"]
    )


@app.get(
    "/status",
    tags=["Status"]
)
async def status(
    db: AsyncSession = Depends(get_db),
    llm_service: MedicalLLMService = Depends(get_llm_service)
):
    """Get service status and configuration."""
    
    return {
        "status": "operational",
        "service": "Smart Reporter (Task 4.5)",
        "llm_config": {
            "use_openai": llm_service.config.use_openai,
            "use_ollama": llm_service.config.use_ollama,
            "openai_model": llm_service.config.openai_model if llm_service.config.use_openai else None,
            "ollama_model": llm_service.config.ollama_model if llm_service.config.use_ollama else None,
            "temperature": llm_service.config.temperature,
            "max_tokens": llm_service.config.max_tokens
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "scripts.smart_reporter_service:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
