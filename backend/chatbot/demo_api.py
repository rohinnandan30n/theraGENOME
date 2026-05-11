"""
TheraGenome AI — Demo API Routes
=================================
FastAPI routes for the demo control panel.
Exposes endpoints to run demo scenarios and get available cases.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any

from backend.chatbot.demo import run_demo_case, get_demo_cases, DEMO_SCENARIOS


# ─────────────────────────────────────────────────────────────────────────
#  Request/Response Models
# ─────────────────────────────────────────────────────────────────────────

class DemoCaseRequest(BaseModel):
    """Request to run a demo scenario."""
    case_id: str = Field(..., description="Demo scenario ID")
    mode: str = Field("doctor", description="Display mode: doctor or patient")
    scope: str = Field("full", description="Explanation scope: full or summary")


class DemoCaseResponse(BaseModel):
    """Response from running a demo scenario."""
    intent: str
    template: str
    scenario: dict[str, Any]
    result: dict[str, Any]
    metadata: dict[str, Any]


class DemoCaseListItem(BaseModel):
    """Single demo case in the list."""
    id: str
    name: str
    description: str
    intent: str


class DemoCaseListResponse(BaseModel):
    """List of available demo scenarios."""
    total: int
    cases: list[DemoCaseListItem]


# ─────────────────────────────────────────────────────────────────────────
#  Router
# ─────────────────────────────────────────────────────────────────────────

demo_router = APIRouter(
    prefix="/api/demo",
    tags=["demo"],
    responses={404: {"description": "Not found"}},
)


# ─────────────────────────────────────────────────────────────────────────
#  Endpoints
# ─────────────────────────────────────────────────────────────────────────

@demo_router.post("/run", response_model=DemoCaseResponse)
async def run_demo(request: DemoCaseRequest) -> dict[str, Any]:
    """
    Run a demo scenario through the pipeline.

    This endpoint:
    1. Validates the case_id
    2. Calls run_demo_case() with specified mode and scope
    3. Returns the structured response

    Parameters
    ----------
    case_id : str
        Demo scenario to run (safe_case, high_risk_case, comparison_case)
    mode : str
        Display mode: doctor (full details) or patient (simplified)
    scope : str
        Explanation scope: full (all details) or summary (key points only)

    Returns
    -------
    dict
        Demo result with DEMO_RESULT template and nested process_query() response
    """
    # Validate case_id
    if request.case_id not in DEMO_SCENARIOS:
        available = list(DEMO_SCENARIOS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown demo case '{request.case_id}'. Available: {available}",
        )

    # Validate mode
    if request.mode not in ("doctor", "patient"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{request.mode}'. Must be 'doctor' or 'patient'",
        )

    # Validate scope
    if request.scope not in ("full", "summary"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope '{request.scope}'. Must be 'full' or 'summary'",
        )

    try:
        result = run_demo_case(
            case_id=request.case_id,
            mode=request.mode,
            scope=request.scope,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running demo case: {str(e)}",
        )


@demo_router.get("/cases", response_model=DemoCaseListResponse)
async def get_demo_cases_list() -> dict[str, Any]:
    """
    Get list of available demo scenarios.

    Returns
    -------
    dict
        List of available demo cases with metadata
    """
    try:
        cases = get_demo_cases()
        return {
            "total": len(cases),
            "cases": cases,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching demo cases: {str(e)}",
        )


@demo_router.get("/info", tags=["demo"])
async def get_demo_info() -> dict[str, Any]:
    """
    Get information about the demo system.

    Returns
    -------
    dict
        Demo system version and capabilities
    """
    return {
        "version": "1.0.0",
        "description": "TheraGenome AI Demo Control Panel",
        "scenarios": len(DEMO_SCENARIOS),
        "modes": ["doctor", "patient"],
        "scopes": ["full", "summary"],
        "endpoints": [
            "/api/demo/run (POST)",
            "/api/demo/cases (GET)",
            "/api/demo/info (GET)",
        ],
    }
