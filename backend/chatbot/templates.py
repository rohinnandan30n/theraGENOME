"""
TheraGenome AI — Response Template System
==========================================
Defines all structured response templates.  The chatbot NEVER returns
human-readable sentences — only template codes + variable maps that a
downstream UI / localisation layer can render.

Template contract
-----------------
Every response has:
- ``template``      : uppercase code (e.g. ``DRUG_NOT_RECOMMENDED``)
- ``variables``     : dict of named values the UI needs to fill slots
- ``explanation``   : ``{reason_codes: [...], modules: {...}}``
- ``metadata``      : timing, mode, model invocation info
"""

from __future__ import annotations

from enum import Enum
from typing import Any


# ──────────────────────────────────────────────
#  Template codes
# ──────────────────────────────────────────────

class TemplateCode(str, Enum):
    """Canonical response template identifiers."""

    # Drug safety
    DRUG_NOT_RECOMMENDED      = "DRUG_NOT_RECOMMENDED"
    DRUG_USE_WITH_CAUTION     = "DRUG_USE_WITH_CAUTION"
    SAFE_TO_USE               = "SAFE_TO_USE"

    # Data input acknowledgement
    GENETIC_DATA_RECEIVED     = "GENETIC_DATA_RECEIVED"
    INFECTION_DATA_RECEIVED   = "INFECTION_DATA_RECEIVED"

    # Comparison
    COMPARISON_RESULT         = "COMPARISON_RESULT"

    # Demo Mode
    DEMO_RESULT               = "DEMO_RESULT"

    # Explanation
    EXPLANATION_SUMMARY       = "EXPLANATION_SUMMARY"
    EXPLANATION_PROVIDED      = "EXPLANATION_PROVIDED"

    # Report Generation
    REPORT_READY              = "REPORT_READY"

    # Safety & Guardrails
    SAFETY_WARNING            = "SAFETY_WARNING"

    # Errors / edge cases
    INSUFFICIENT_CONTEXT      = "INSUFFICIENT_CONTEXT"
    REQUIRE_MORE_DATA         = "REQUIRE_MORE_DATA"
    REQUEST_MISSING_INFO      = "REQUEST_MISSING_INFO"
    UNSUPPORTED_QUERY         = "UNSUPPORTED_QUERY"
    MODEL_ERROR               = "MODEL_ERROR"
    GENERAL_RESPONSE          = "GENERAL_RESPONSE"


# ──────────────────────────────────────────────
#  Template builder
# ──────────────────────────────────────────────

def build_response(
    intent: str,
    template: TemplateCode,
    variables: dict[str, Any],
    reason_codes: list[str],
    reason_details: list[dict[str, str]],
    modules: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Assemble a canonical chatbot response envelope.

    Parameters
    ----------
    intent : str
        Detected intent value.
    template : TemplateCode
        Which template the UI should render.
    variables : dict
        Named slots the UI will interpolate.
    reason_codes : list[str]
        Machine-readable rationale (always present in both modes).
    reason_details : list[dict]
        Fine-grained clinical rationales with module and severity maps.
    modules : dict
        Raw model outputs (stripped by mode filter in patient mode).
    metadata : dict, optional
        Extra metadata (timing, versions, etc.).

    Returns
    -------
    dict
        JSON-serialisable response envelope.
    """
    return {
        "intent": intent,
        "template": template.value,
        "variables": variables,
        "explanation": {
            "reason_codes": reason_codes,
            "reason_details": reason_details,
            "modules": modules,
        },
        "metadata": metadata or {},
    }
