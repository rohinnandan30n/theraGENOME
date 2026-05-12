"""
TheraGenome AI — Chatbot Controller
=====================================
Top-level orchestrator that wires together:

1. Intent detection
2. Module routing
3. Decision engine
4. Response formatting

Exposes a single ``process_query()`` function and, optionally, a
FastAPI router for HTTP serving.
"""

from __future__ import annotations

import time
from typing import Any

from backend.chatbot.intent_detector import IntentDetector
from backend.chatbot.router import ModuleRouter
from backend.chatbot.decision_engine import DecisionEngine
from backend.chatbot.mode_filter import ModeFilter
from backend.chatbot.explainer import ExplainerEngine
from backend.chatbot.context_validator import ContextValidator
from backend.chatbot.guidance import get_missing_fields, build_guidance_response
from backend.chatbot.guardrails import SafetyGuardrails
from backend.chatbot.templates import TemplateCode
import uuid

# ──────────────────────────────────────────────
#  Core engine (framework-agnostic)
# ──────────────────────────────────────────────

# Singletons — instantiated once, reused per request (thread-safe).
_intent_detector = IntentDetector()
_router = ModuleRouter()
_decision_engine = DecisionEngine()
_mode_filter = ModeFilter()
_explainer = ExplainerEngine()
_context_validator = ContextValidator()
_guardrails = SafetyGuardrails()

_RESPONSE_CACHE: dict[str, dict[str, Any]] = {}


def process_query(
    user_input: str,
    mode: str = "doctor",
    context: dict[str, Any] | None = None,
    scope: str = "full",
) -> dict[str, Any]:
    """
    End-to-end chatbot query processing.

    Parameters
    ----------
    user_input : str
        Raw text from the user.
    mode : str
        ``"doctor"`` — full clinical detail.
        ``"patient"`` — simplified, safe-for-patient output.
    context : dict, optional
        Structured context (drug names, genetic data payload, etc.).

    Returns
    -------
    dict
        Canonical response envelope::

            {
                "intent": "...",
                "template": "...",
                "variables": {...},
                "data": {...},
                "metadata": {...}
            }
    """
    context = context or {}
    start = time.perf_counter()

    # 1. SAFETY GUARDRAILS CHECK (RUNS FIRST)
    safety_flag = _guardrails.check(user_input, context)
    if safety_flag.triggered:
        response = _guardrails.get_safety_response(safety_flag)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.setdefault("metadata", {}).update({
            "processing_time_ms": elapsed_ms,
            "mode": mode,
            "intent_confidence": 0.0,  # Safety checks don't have intent confidence
        })
        return response

    # 2. Detect intent
    intent_result = _intent_detector.detect(user_input)

    # 3. Intercept Explanation Requests (special handling)
    if intent_result.intent == "explain_result":
        valid_response = _context_validator.validate_last_response(context)
        if isinstance(valid_response, dict):
            response = valid_response
        else:
            linked_id = valid_response.metadata.get("linked_response_id")
            cached_full = _RESPONSE_CACHE.get(linked_id) if linked_id else None
            context_to_use = cached_full if cached_full else valid_response.model_dump()
            response = _explainer.explain({"last_response": context_to_use, "scope": scope}, scope=scope)
    else:
        # 4. Add user_input to context for model extraction (gene names, drug names, pathogens)
        context.setdefault("user_input", user_input)
        
        # 4. Route to models (catches domain-specific errors like missing "drugs" for compare_drugs)
        route_result = _router.route(intent_result.intent, context)
        
        # 5. Check if routing had errors — return REQUIRE_MORE_DATA before checking guidance
        if route_result.errors:
            response = {
                "intent": intent_result.intent.value,
                "template": TemplateCode.REQUIRE_MORE_DATA.value,
                "variables": {
                    "errors": route_result.errors,
                    "missing_fields": [err.get("error", "unknown") for err in route_result.errors],
                },
                "explanation": {
                    "reason_codes": ["missing_required_input"],
                    "reason_details": [],
                },
                "metadata": {},
            }
        else:
            # 6. Check for missing required fields (Guidance Engine) — only if routing succeeded
            missing_fields = get_missing_fields(context, intent=intent_result.intent.value)
            
            if missing_fields:
                # Halt normal pipeline and request missing info
                response = build_guidance_response(missing_fields)
            else:
                # 7. Decision + template selection
                response = _decision_engine.evaluate(route_result)

                # Cache full response
                response_id = str(uuid.uuid4())
                response.setdefault("metadata", {})["linked_response_id"] = response_id
                import copy
                _RESPONSE_CACHE[response_id] = copy.deepcopy(response)

    # 8. Apply Mode Filter
    response = _mode_filter.apply(response, mode=mode)

    # 9. Attach timing + intent metadata
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.setdefault("metadata", {}).update({
        "processing_time_ms": elapsed_ms,
        "intent_confidence": intent_result.confidence,
        "matched_keywords": intent_result.matched_keywords,
    })

    return response


# ──────────────────────────────────────────────
#  FastAPI router (optional — only used when
#  the server imports this module)
# ──────────────────────────────────────────────

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field

    class ChatbotRequest(BaseModel):
        input: str = Field(..., min_length=1, description="User query text")
        mode: str = Field("doctor", pattern=r"^(doctor|patient)$")
        context: dict[str, Any] = Field(default_factory=dict)
        scope: str = Field("full", description="Explanation scope filter")

    class DrugInteractionRequest(BaseModel):
        drug: str = Field(..., min_length=1, description="Drug name")
        organ: str = Field(..., min_length=1, description="Organ or system name")

    class DrugInteractionResponse(BaseModel):
        drug: str
        organ: str
        toxicity: str
        description: str
        reversible: bool

    from backend.chatbot.schemas import ChatbotResponse

    api_router = APIRouter(prefix="/api/v1/chatbot", tags=["chatbot"])

    @api_router.post(
        "/query",
        response_model=ChatbotResponse,
        summary="Process a chatbot query",
        description="Detects intent, routes to AI models, and returns a structured JSON response.",
    )
    async def chatbot_query(req: ChatbotRequest) -> ChatbotResponse:
        try:
            result = process_query(
                user_input=req.input,
                mode=req.mode,
                context=req.context,
                scope=req.scope,
            )
            return ChatbotResponse(**result)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @api_router.post(
        "/drug-interactions",
        response_model=DrugInteractionResponse,
        summary="Get drug-organ interaction data",
        description="Queries the database for drug safety and toxicity information for a specific organ.",
    )
    async def get_drug_interaction(req: DrugInteractionRequest) -> DrugInteractionResponse:
        try:
            from backend.database import query_drug_safety
            
            # Query database for drug safety data
            results = query_drug_safety(drug_name=req.drug)
            
            # Filter by organ system
            organ_lower = req.organ.lower()
            organ_map = {
                'heart': 'cardiac', 'cardiac': 'cardiac',
                'kidney': 'renal', 'renal': 'renal', 'kidneys': 'renal',
                'liver': 'hepatic', 'hepatic': 'hepatic',
                'lung': 'respiratory', 'lungs': 'respiratory', 'respiratory': 'respiratory',
                'digestive': 'gastrointestinal', 'gastrointestinal': 'gastrointestinal', 'gi': 'gastrointestinal',
                'brain': 'nervous', 'nervous': 'nervous',
                'stomach': 'gastrointestinal',
                'pancreas': 'endocrine', 'endocrine': 'endocrine',
            }
            
            target_organ = organ_map.get(organ_lower, organ_lower)
            
            # Find matching interaction
            matching_result = None
            for result in results:
                if result.get('organ_system', '').lower() == target_organ:
                    matching_result = result
                    break
            
            if not matching_result and results:
                # Use first available result if no exact match
                matching_result = results[0]
            
            if not matching_result:
                return DrugInteractionResponse(
                    drug=req.drug,
                    organ=req.organ,
                    toxicity="low",
                    description=f"No specific interaction data found for {req.drug} in {req.organ}.",
                    reversible=True
                )
            
            return DrugInteractionResponse(
                drug=req.drug,
                organ=req.organ,
                toxicity=matching_result.get("toxicity_level", "low").lower(),
                description=matching_result.get("description", ""),
                reversible=matching_result.get("reversible", True)
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

except ImportError:
    # FastAPI not installed — pure-library mode.
    api_router = None  # type: ignore[assignment]
