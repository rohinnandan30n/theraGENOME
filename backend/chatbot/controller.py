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

except ImportError:
    # FastAPI not installed — pure-library mode.
    api_router = None  # type: ignore[assignment]
