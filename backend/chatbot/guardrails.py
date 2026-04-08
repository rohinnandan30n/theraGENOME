"""
TheraGenome AI — Safety & Guardrails Engine
============================================
Detects unsafe, dangerous, or high-risk medical queries and returns
structured safety responses BEFORE processing.

Design
------
The guardrails engine is a *deterministic detector* that:
1. Runs FIRST in the processing pipeline
2. Returns early if unsafe query detected
3. Does NOT modify normal pipeline logic
4. Does NOT generate natural language warnings
5. Returns structured JSON only (frontend handles rendering)

Trigger Categories
------------------
- EMERGENCY: Life-threatening symptoms
- SELF_MEDICATION_RISK: Requesting self-medication without doctor input
- INSUFFICIENT_CONTEXT_CRITICAL: Missing critical data for high-risk decisions
- HIGH_UNCERTAINTY: Query too vague for reliable recommendations

Action Codes
------------
- SEEK_IMMEDIATE_HELP: Call emergency services
- CONSULT_DOCTOR: Must consult healthcare provider
- PROVIDE_MORE_INFO: Additional context needed
- LIMITED_ASSISTANCE: System cannot assist safely
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


# ──────────────────────────────────────────────
#  Safety trigger patterns
# ──────────────────────────────────────────────

# Emergency symptoms that require immediate medical attention
_EMERGENCY_PATTERNS = [
    # Cardiovascular emergencies
    r"\bchest\s*(pain|tightness|pressure)\b",
    r"\bheart\s*attack\b",
    r"\bcan't\s*breathe\b",
    r"\bdifficulty\s*breathing\b",
    r"\bstroke\b",
    # Severe bleeding
    r"\b(severe|uncontrolled).*bleed",  # No word boundary at end to catch "bleeding"
    # Other emergencies
    r"\banaphyla",
    r"\bunconsciou",
    r"\boverdose\b",
]

# Self-medication risks (requesting drugs without medical supervision)
_SELF_MEDICATION_PATTERNS = [
    # Must explicitly mention "without doctor" or similar
    r"\b(what|which|give|prescribe).{0,30}(without|no|alone|myself).{0,20}(doctor|physician|supervision|nurse|pharmacist)",
    r"\b(can\s*i\s*(take|use|give)).{0,30}(without|no|alone|myself).{0,20}(doctor|physician|supervision|consultation)",
    # Specific drug + without supervision context
    r"\b(should|can|may|could)\s*(i|you)\s*(take|use).{0,20}\b(without|no)\b.{0,20}(doctor|physician|consultation|prescription)",
]

# Patterns indicating missing critical context
_INSUFFICIENT_CONTEXT_PATTERNS = [
    # Requesting decision without genetic info for pharmacogenomic drugs
    r"\b(should\s*i\s*take|is\s*it\s*safe).*?\b(tramadol|codeine|warfarin|clopidogrel)\b(?!.*genetic|cyp\d)",
    # Requesting decision without infection info for antibiotics
    r"\b(which\s*antibiotic|treat\s*my\s*infection|what\s*drug)(?!.*culture|pathogen|sensitivity)",
]

# High uncertainty queries (too vague for reliable recommendations)
_HIGH_UNCERTAINTY_PATTERNS = [
    # Extremely vague symptoms
    r"^\s*(i\s*feel\s*bad|something\s*is\s*wrong|help|i'm\s*sick)\s*$",
    # Multiple unrelated symptoms without context
    r"\b(also\s*have|also\s*experiencing|and\s*then|and\s*also).{1,30}(also|and)\b",
    # Requesting medical diagnosis (not within scope)
    r"\b(do\s*i\s*have|am\s*i|what\s*is\s*wrong|what\s*disease|what\s*condition).*?(\?|$)",
]


# ──────────────────────────────────────────────
#  Safety detection
# ──────────────────────────────────────────────

@dataclass
class SafetyFlag:
    """Result of safety check."""
    triggered: bool
    trigger_type: str | None = None  # EMERGENCY, SELF_MEDICATION_RISK, etc.
    action_code: str | None = None   # SEEK_IMMEDIATE_HELP, CONSULT_DOCTOR, etc.
    severity: str | None = None      # high, medium, low
    confidence: float = 0.0          # 0.0 – 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "triggered": self.triggered,
            "trigger_type": self.trigger_type,
            "action_code": self.action_code,
            "severity": self.severity,
            "confidence": round(self.confidence, 4),
        }


def _check_emergency(user_input: str) -> tuple[bool, float]:
    """
    Detect life-threatening medical emergencies.
    
    Returns (is_emergency, confidence)
    """
    text = user_input.lower()
    
    for pattern in _EMERGENCY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            return True, 0.95
    
    return False, 0.0


def _check_self_medication_risk(user_input: str) -> tuple[bool, float]:
    """
    Detect queries requesting self-medication without medical supervision.
    
    Returns (is_risky, confidence)
    """
    text = user_input.lower()
    
    for pattern in _SELF_MEDICATION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            return True, 0.85
    

    return False, 0.0


def _check_insufficient_critical_context(
    user_input: str,
    context: dict[str, Any] | None = None,
) -> tuple[bool, float]:
    """
    Detect high-risk decisions with missing critical context.
    
    Returns (insufficient, confidence)
    """
    text = user_input.lower()
    context = context or {}
    
    # Check for high-risk drugs without genetic data
    pharmacogenomic_drugs = ["tramadol", "codeine", "warfarin", "clopidogrel", "citalopram"]
    if any(drug in text for drug in pharmacogenomic_drugs):
        if "genetic_data" not in context:
            return True, 0.80
    
    # Check for antibiotic choice without infection info
    antibiotics = ["antibiotic", "amoxicillin", "ciprofloxacin", "azithromycin"]
    if any(antibiotic in text for antibiotic in antibiotics):
        if re.search(r"\b(treat|infection|bacteria|pathogen)\b", text):
            if "infection_data" not in context:
                return True, 0.75
    
    return False, 0.0


def _check_high_uncertainty(user_input: str, context: dict[str, Any] | None = None) -> tuple[bool, float]:
    """
    Detect queries too vague for reliable recommendations.
    
    Returns (too_vague, confidence)
    """
    text = user_input.lower().strip()
    context = context or {}
    
    # Don't flag empty input as uncertainty — let intent detector classify it as general_query
    if not text:
        return False, 0.0
    
    # Don't flag short follow-up questions if there's a context (e.g., "Why?" after a previous result)
    if len(text) < 10 and "last_response" in context:
        return False, 0.0
    
    # Don't flag explanation-related single words/short phrases (Why, Explain, How, etc.)
    explanation_patterns = [r"\bwhy\b", r"\bexplain\b", r"\bhow\b", r"\breason\b", r"\binterpret\b"]
    if any(re.search(p, text, re.IGNORECASE) for p in explanation_patterns):
        return False, 0.0
    
    # Check vague patterns
    for pattern in _HIGH_UNCERTAINTY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            return True, 0.70
    
    # Also flag if input is extremely short without specifics
    if len(text) < 10 and not re.search(r"\b(drug|medicine|disease|condition|symptom)\b", text):
        return True, 0.60
    
    return False, 0.0


# ──────────────────────────────────────────────
#  Guardrails engine
# ──────────────────────────────────────────────

class SafetyGuardrails:
    """
    Stateless safety guardrails engine.
    
    Detects unsafe queries and returns early with safety responses,
    preventing them from entering the normal processing pipeline.
    
    Usage::
    
        guardrails = SafetyGuardrails()
        flag = guardrails.check(user_input="...", context={...})
        if flag.triggered:
            return guardrails.get_safety_response(flag)
    """
    
    def check(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
    ) -> SafetyFlag:
        """
        Check if user input triggers any safety guardrails.
        
        Parameters
        ----------
        user_input : str
            Raw user query.
        context : dict, optional
            Current context (drug names, genetic data, etc.).
        
        Returns
        -------
        SafetyFlag
            Safety check result with trigger type and action code.
        """
        context = context or {}
        
        # 1. Check for life-threatening emergencies (highest priority)
        is_emergency, confidence = _check_emergency(user_input)
        if is_emergency:
            return SafetyFlag(
                triggered=True,
                trigger_type="EMERGENCY",
                action_code="SEEK_IMMEDIATE_HELP",
                severity="high",
                confidence=confidence,
            )
        
        # 2. Check for self-medication risks
        is_self_med_risk, confidence = _check_self_medication_risk(user_input)
        if is_self_med_risk:
            return SafetyFlag(
                triggered=True,
                trigger_type="SELF_MEDICATION_RISK",
                action_code="CONSULT_DOCTOR",
                severity="high",
                confidence=confidence,
            )
        
        # 3. Check for missing critical context
        insufficient, confidence = _check_insufficient_critical_context(user_input, context)
        if insufficient:
            return SafetyFlag(
                triggered=True,
                trigger_type="INSUFFICIENT_CONTEXT_CRITICAL",
                action_code="PROVIDE_MORE_INFO",
                severity="medium",
                confidence=confidence,
            )
        
        # 4. Check for high uncertainty
        too_vague, confidence = _check_high_uncertainty(user_input, context)
        if too_vague:
            return SafetyFlag(
                triggered=True,
                trigger_type="HIGH_UNCERTAINTY",
                action_code="PROVIDE_MORE_INFO",
                severity="low",
                confidence=confidence,
            )
        
        # No guardrails triggered
        return SafetyFlag(triggered=False, confidence=1.0)
    
    def get_safety_response(self, flag: SafetyFlag) -> dict[str, Any]:
        """
        Build structured safety response from a triggered guardrail.
        
        Parameters
        ----------
        flag : SafetyFlag
            Safety flag with trigger details.
        
        Returns
        -------
        dict
            Structured response envelope with safety information.
        """
        if not flag.triggered:
            return {}
        
        return {
            "intent": "safety_guardrail",
            "template": "SAFETY_WARNING",
            "variables": {
                "type": flag.trigger_type,
            },
            "safety": {
                "severity": flag.severity,
                "action_code": flag.action_code,
            },
            "metadata": {
                "source": "guardrails",
                "confidence": flag.confidence,
            },
        }
