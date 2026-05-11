"""
TheraGenome AI — Input Guidance Engine
========================================
Detects missing critical inputs for drug analysis and generates guidance.
"""

from typing import Any
from backend.chatbot.requirements import REQUIRED_FIELDS
from backend.chatbot.templates import TemplateCode


def get_missing_fields(context: dict[str, Any], intent: str | None = None) -> list[str]:
    """
    Check if critical fields are missing for drug analysis intents.
    
    Only triggers guidance for complex medical decision intents (compare_drugs).
    Basic drug_analysis queries (safety/contraindication) don't need genetic/infection data.
    
    Parameters
    ----------
    context : dict
        User context
    intent : str, optional
        Detected intent (if available)
    
    Returns
    -------
    list[str]
        Missing field keys, or empty list if guidance not needed.
    """
    # Only require fields for compare_drugs (drug comparison needs patient data)
    # Basic drug_analysis (safety, toxicity, allergies) can proceed without genetic/infection data
    complex_intents = {"compare_drugs"}
    
    # If intent is provided, check if it's a complex intent
    if intent and intent not in complex_intents:
        return []
    
    # Check for missing required fields
    missing = []
    for field in REQUIRED_FIELDS:
        if field not in context or not context[field]:
            missing.append(field)
    
    return missing


def build_guidance_response(missing_fields: list[str]) -> dict[str, Any]:
    """
    Build structured guidance response for missing fields.
    """
    guidance_questions = [
        {
            "field": field,
            "question_code": REQUIRED_FIELDS[field]
        }
        for field in missing_fields
    ]
    
    return {
        "intent": "input_guidance",
        "template": "REQUEST_MISSING_INFO",
        "variables": {
            "missing_fields": missing_fields
        },
        "explanation": {
            "reason_codes": ["missing_required_fields"],
            "reason_details": [],
            "modules": {}
        },
        "guidance": guidance_questions,
        "metadata": {
            "source": "guidance_engine"
        }
    }
