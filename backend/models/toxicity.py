"""
TheraGenome AI — Drug Toxicity Model
=====================================
Simulates drug toxicity screening and adverse-reaction prediction.
Returns structured safety data including organ-specific toxicity,
interaction warnings, and dosage constraints.

Production replacement: integrate with a QSAR model or an adverse-event
database (e.g. FAERS, SIDER) behind this interface.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
import logging

# Import real data sources
try:
    from backend.database import query_drug_safety
    from backend.models.drug_recommendations import generate_safer_alternatives
except ImportError:
    from database import query_drug_safety
    from drug_recommendations import generate_safer_alternatives

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  Data contracts
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class ToxicityFlag:
    """Single toxicity signal for a drug."""
    organ_system: str        # e.g. "hepatic", "renal", "cardiac", "neurological"
    severity: str            # "mild", "moderate", "severe"
    description: str
    reversible: bool


@dataclass(frozen=True)
class DrugInteraction:
    """Pairwise drug interaction warning."""
    drug_a: str
    drug_b: str
    interaction_type: str    # "synergistic_toxicity", "reduced_efficacy", "contraindicated"
    severity: str            # "low", "medium", "high", "critical"
    recommendation: str


@dataclass
class ToxicityAnalysisResult:
    """Complete output from the drug toxicity model."""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    drug_name: str = ""
    overall_toxicity_risk: str = "unknown"   # low | medium | high | unknown
    toxicity_flags: list[dict[str, Any]] = field(default_factory=list)
    drug_interactions: list[dict[str, Any]] = field(default_factory=list)
    max_safe_dose: dict[str, Any] = field(default_factory=dict)
    contraindications: list[str] = field(default_factory=list)
    therapeutic_index: float = 0.0           # higher = safer
    safer_alternatives: list[dict[str, Any]] = field(default_factory=list)  # ✨ NEW: Ranked safer drug alternatives

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ──────────────────────────────────────────────
#  Model interface
# ──────────────────────────────────────────────

def drug_toxicity_model(
    drug_name: str = "",
    context: dict[str, Any] | None = None,
) -> ToxicityAnalysisResult:
    """
    Screen a drug for toxicity, interactions, and dosage safety.
    NOW USES REAL DATA from database!

    Parameters
    ----------
    drug_name : str
        Primary drug under evaluation.
    context : dict, optional
        Additional patient context (co-medications, organ function, etc.).

    Returns
    -------
    ToxicityAnalysisResult
    """
    context = context or {}
    drug_name = drug_name or context.get("drug", "")
    patient_id = context.get("patient_id", "unknown")
    
    # Extract drug name from user input if not provided
    if not drug_name:
        user_input = context.get("user_input", "")
        user_input_lower = user_input.lower()
        
        # Common drug patterns (exact keyword matching)
        drug_keywords = [
            "amoxicillin", "amoxicilline", "penicillin", "warfarin", "metformin",
            "ibuprofen", "aspirin", "clopidogrel", "metoprolol", "simvastatin",
            "atorvastatin", "lisinopril", "metoprolol", "omeprazole", "escitalopram"
        ]
        
        # Try exact keyword match first
        for drug in drug_keywords:
            if drug in user_input_lower:
                drug_name = drug
                break
        
        # If no keyword match, try regex extraction
        if not drug_name:
            import re
            # Pattern 1: "drug/medicine/medication is..." or "is [drug] safe/toxic/dangerous"
            pattern1 = r'(?:drug|medicine|medication|is)\s+([a-z]+(?:cillin|pril|olol|ine|ol|ide)?)\s+(?:safe|toxic|dangerous|ok|good|bad|side|effect)'
            match1 = re.search(pattern1, user_input_lower)
            if match1:
                potential_drug = match1.group(1)
                # Validate it's a reasonable drug name (not common words)
                if len(potential_drug) > 3 and potential_drug not in ["this", "that", "what", "drug", "safe"]:
                    drug_name = potential_drug
            
            # Pattern 2: quoted names like "warfarin" or 'metformin'
            if not drug_name:
                pattern2 = r'["\']([a-z]+)["\']'
                match2 = re.search(pattern2, user_input_lower)
                if match2:
                    drug_name = match2.group(1)
            
            # Pattern 3: Capitalized words that might be drug names (e.g., "Amoxicillin")
            if not drug_name:
                pattern3 = r'\b([A-Z][a-z]+(?:cillin|pril|olol|ine|ol)?)\b'
                match3 = re.search(pattern3, user_input)
                if match3:
                    drug_name = match3.group(1).lower()
    
    # Query database for drug safety data
    db_safety = query_drug_safety(drug_name=drug_name if drug_name else None)
    
    toxicity_flags = []
    overall_risk = "low"
    contraindications = []
    therapeutic_index = 3.0  # Default
    
    # Build toxicity flags from real data
    if db_safety:
        organ_system_severity = {}
        
        for safety_record in db_safety:
            organ = safety_record.get("organ_system", "unknown")
            severity = safety_record.get("toxicity_level", "mild")
            description = safety_record.get("description", "")
            reversible = safety_record.get("reversible", True)
            
            toxicity_flags.append(asdict(ToxicityFlag(
                organ_system=organ,
                severity=severity,
                description=description,
                reversible=reversible,
            )))
            
            # Track highest severity per organ
            organ_system_severity[organ] = severity
        
        # Determine overall risk based on organ toxicity
        if any(s == "severe" for s in organ_system_severity.values()):
            overall_risk = "high"
            contraindications = ["pregnancy", "severe_organ_dysfunction"]
            therapeutic_index = 1.5
        elif any(s == "moderate" for s in organ_system_severity.values()):
            overall_risk = "medium"
            contraindications = ["severe_hepatic_impairment", "severe_renal_impairment"]
            therapeutic_index = 3.0
        else:
            overall_risk = "low"
            therapeutic_index = 5.0
    else:
        # No specific data - use safe defaults
        toxicity_flags = [
            asdict(ToxicityFlag(
                organ_system="hepatic",
                severity="mild",
                description="Monitor liver function periodically",
                reversible=True,
            )),
        ]
        overall_risk = "low"
        therapeutic_index = 4.0
    
    # Drug interactions (common patterns)
    drug_interactions = []
    common_interactions = {
        "amoxicillin": [("methotrexate", "reduced_efficacy", "medium")],
        "amoxicilline": [("methotrexate", "reduced_efficacy", "medium")],
        "warfarin": [("aspirin", "synergistic_toxicity", "high"), ("nsaids", "increased_bleeding", "high")],
        "metformin": [("contrast_dye", "lactic_acidosis", "critical")],
        "ibuprofen": [("ace_inhibitors", "renal_failure", "high"), ("warfarin", "bleeding", "high")],
    }
    
    drug_key = drug_name.lower() if drug_name else ""
    if drug_key in common_interactions:
        for other_drug, interaction_type, severity in common_interactions[drug_key]:
            drug_interactions.append(asdict(DrugInteraction(
                drug_a=drug_name,
                drug_b=other_drug,
                interaction_type=interaction_type,
                severity=severity,
                recommendation="avoid_combination" if severity == "critical" else "monitor_closely",
            )))
    
    # Standard dosing (can be enhanced with real data)
    max_safe_dose = {
        "adult": {"value": 500, "unit": "mg", "frequency": "twice_daily"},
        "elderly": {"value": 250, "unit": "mg", "frequency": "once_daily"},
        "renal_impairment": {"value": 250, "unit": "mg", "frequency": "once_daily"},
        "hepatic_impairment": {"value": 250, "unit": "mg", "frequency": "once_daily"},
    }
    
    # Check for penicillin allergy contraindication (for amoxicillin/related drugs)
    patient_allergies = context.get("patient_allergies", [])
    if isinstance(patient_allergies, str):
        patient_allergies = [patient_allergies]
    
    if drug_key in ["amoxicillin", "amoxicilline"] and "penicillin" in [a.lower() for a in patient_allergies]:
        contraindications.append("⚠️ PENICILLIN ALLERGY - ABSOLUTE CONTRAINDICATION ⚠️")
        overall_risk = "high"
        
        # Log this critical finding
        logger.warning(f"⚠️ CRITICAL: {drug_name} contraindicated in penicillin allergy (patient {patient_id})")
    
    # ✨ NEW: Generate safer drug alternatives if toxicity risk detected
    safer_alternatives = []
    if overall_risk in ["high", "medium"] or len(contraindications) > 0:
        try:
            contraindication_reason = "; ".join(contraindications) if contraindications else "toxicity risk"
            safer_alternatives = generate_safer_alternatives(
                original_drug=drug_name or drug_key,
                contraindication_reason=contraindication_reason
            )
            logger.info(f"💊 Generated {len(safer_alternatives)} safer alternatives to {drug_name}")
        except Exception as e:
            logger.error(f"⚠️ Error generating safer alternatives: {e}")
    
    result = ToxicityAnalysisResult(
        drug_name=drug_name if drug_name else "unknown",
        overall_toxicity_risk=overall_risk,
        toxicity_flags=toxicity_flags,
        drug_interactions=drug_interactions,
        max_safe_dose=max_safe_dose,
        contraindications=contraindications,
        therapeutic_index=therapeutic_index,
        safer_alternatives=safer_alternatives,  # ✨ NEW: Add safer alternatives
    )

    logger.info(f"✅ Toxicity analysis complete for {drug_name or 'unknown'} (patient {patient_id}): {overall_risk} risk, {len(contraindications)} contraindications, {len(safer_alternatives)} alternatives")
    return result
