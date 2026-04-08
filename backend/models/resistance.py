"""
TheraGenome AI — Antibiotic Resistance Model
=============================================
Simulates antibiotic resistance profiling for infectious pathogens.
Returns structured susceptibility data, resistance mechanisms, and
treatment recommendations.

Production replacement: wrap an AMR gene detection pipeline
(e.g. ResFinder, CARD-RGI) behind this same interface.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
import logging

# Import real data sources
try:
    from backend.database import query_resistance_markers
except ImportError:
    from database import query_resistance_markers

logger = logging.getLogger(__name__)



# ──────────────────────────────────────────────
#  Pathogen extraction helper
# ──────────────────────────────────────────────

def extract_pathogen_from_input(user_input: str) -> str | None:
    """
    Extract pathogen/organism name from user input using pattern matching.
    
    Examples:
    - "What antibiotics for MRSA?" → "MRSA"
    - "How to treat Pseudomonas aeruginosa?" → "Pseudomonas aeruginosa"
    - "Best drug for gram-negative bacteria?" → "gram-negative"
    """
    if not user_input:
        return None
    
    # Pathogen patterns (case-insensitive)
    patterns = [
        r'\b(MRSA|VRSA|VRE|CDI|ESBL)\b',
        r'\b(Staphylococcus\s+aureus|Pseudomonas\s+aeruginosa|Escherichia\s+coli|Klebsiella\s+pneumoniae|Acinetobacter\s+baumannii)\b',
        r'\b(gram[\s\-]*(positive|negative))',
        r'\b(vancomycin[\s\-]?resistant|methicillin[\s\-]?resistant)',
        r'\b(Clostridium\s+difficile|Mycobacterium\s+tuberculosis)\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            pathogen = match.group(0).strip()
            logger.info(f"🦠 Extracted pathogen: {pathogen}")
            return pathogen
    
    return None


# ──────────────────────────────────────────────
#  Data contracts
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class ResistanceMarker:
    """Single resistance gene / mechanism detected."""
    gene: str
    mechanism: str           # e.g. "efflux_pump", "target_modification", "enzymatic_inactivation"
    antibiotic_class: str    # e.g. "beta_lactam", "fluoroquinolone"
    confidence: float        # 0.0 – 1.0


@dataclass
class ResistanceAnalysisResult:
    """Complete output from the antibiotic resistance model."""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    pathogen_identified: str = ""
    susceptibility_profile: dict[str, str] = field(default_factory=dict)
    resistance_markers: list[dict[str, Any]] = field(default_factory=list)
    recommended_antibiotics: list[str] = field(default_factory=list)
    avoid_antibiotics: list[str] = field(default_factory=list)
    overall_resistance_risk: str = "unknown"  # low | medium | high | unknown

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ──────────────────────────────────────────────
#  Model interface
# ──────────────────────────────────────────────

def antibiotic_resistance_model(context: dict[str, Any] | None = None) -> ResistanceAnalysisResult:
    """
    Analyse pathogen data for antibiotic resistance patterns.
    NOW USES REAL DATA from database!
    Extracts pathogen names from user input and queries real resistance markers.

    Parameters
    ----------
    context : dict, optional
        Expected keys:
        - ``infection_data``: culture / sequencing results
        - ``pathogen``:       suspected or confirmed organism
        - ``user_input``:     raw user query (for pathogen extraction)

    Returns
    -------
    ResistanceAnalysisResult
    """
    context = context or {}
    
    # Extract infection/pathogen data
    infection_data = context.get("infection_data", {})
    user_input = context.get("user_input", "")
    patient_id = context.get("patient_id", "unknown")
    
    # Try to extract pathogen from user input first
    extracted_pathogen = extract_pathogen_from_input(user_input)
    
    # Fall back to context pathogen if extraction failed
    pathogen = extracted_pathogen or context.get("pathogen", "Unknown organism")
    
    logger.info(f"🔍 Analyzing resistance for: {pathogen}")
    
    # Query database for resistance markers
    db_markers = query_resistance_markers(organism=pathogen)
    
    # Build resistance markers from database
    resistance_markers = []
    susceptibility_profile = {}
    recommended_antibiotics = set()
    avoid_antibiotics = set()
    overall_risk = "low"
    
    if db_markers:
        # Use real resistance data from database
        for marker in db_markers:
            gene = marker.get("gene", "unknown")
            mechanism = marker.get("mechanism", "unknown")
            antibiotic_class = marker.get("antibiotic_class", "unknown")
            confidence = marker.get("confidence", 0.8)
            
            resistance_markers.append(asdict(ResistanceMarker(
                gene=gene,
                mechanism=mechanism,
                antibiotic_class=antibiotic_class,
                confidence=confidence,
            )))
            
            # Mark antibiotic class as resistant
            susceptibility_profile[antibiotic_class] = "resistant"
            avoid_antibiotics.add(antibiotic_class)
            overall_risk = "high"
        
        logger.info(f"✅ Found {len(db_markers)} resistance markers in database")
    
    # If no specific data, use intelligent defaults based on pathogen
    if not resistance_markers:
        if "MRSA" in pathogen or "aureus" in pathogen:
            logger.info(f"🔬 Using MRSA defaults for: {pathogen}")
            resistance_markers = [
                asdict(ResistanceMarker(
                    gene="mecA",
                    mechanism="target_modification",
                    antibiotic_class="beta_lactam",
                    confidence=0.95,
                )),
            ]
            susceptibility_profile = {
                "vancomycin": "susceptible",
                "linezolid": "susceptible",
                "daptomycin": "susceptible",
                "beta_lactam": "resistant",
            }
            recommended_antibiotics = {"vancomycin", "linezolid", "daptomycin"}
            avoid_antibiotics = {"beta_lactam", "penicillin", "ampicillin"}
            overall_risk = "high"
        elif "Pseudomonas" in pathogen or "gram-negative" in pathogen.lower():
            logger.info(f"🔬 Using gram-negative defaults for: {pathogen}")
            susceptibility_profile = {
                "fluoroquinolone": "susceptible",
                "cephalosporin": "intermediate",
                "aminoglycoside": "susceptible",
                "carbapenems": "susceptible",
            }
            recommended_antibiotics = {"fluoroquinolone", "aminoglycoside", "carbapenems"}
            avoid_antibiotics = set()
            overall_risk = "medium"
        elif "VRE" in pathogen or "vancomycin" in pathogen.lower():
            logger.info(f"🔬 Using VRE defaults for: {pathogen}")
            resistance_markers = [
                asdict(ResistanceMarker(
                    gene="vanA",
                    mechanism="target_modification",
                    antibiotic_class="glycopeptide",
                    confidence=0.92,
                )),
            ]
            susceptibility_profile = {
                "vancomycin": "resistant",
                "linezolid": "susceptible",
                "doxycycline": "susceptible",
            }
            recommended_antibiotics = {"linezolid", "doxycycline", "chloramphenicol"}
            avoid_antibiotics = {"vancomycin", "glycopeptides"}
            overall_risk = "high"
        else:
            logger.info(f"ℹ️ Using general defaults for: {pathogen}")
            overall_risk = "low"
            recommended_antibiotics = {"broad_spectrum_beta_lactam"}
    else:
        # Recommend alternatives for resistant classes
        if "beta_lactam" in avoid_antibiotics:
            recommended_antibiotics.update({"fluoroquinolone", "macrolide", "aminoglycoside"})
        if "fluoroquinolone" in avoid_antibiotics:
            recommended_antibiotics.update({"beta_lactam", "aminoglycoside", "macrolide"})
    
    result = ResistanceAnalysisResult(
        pathogen_identified=pathogen,
        susceptibility_profile=susceptibility_profile,
        resistance_markers=resistance_markers,
        recommended_antibiotics=list(recommended_antibiotics),
        avoid_antibiotics=list(avoid_antibiotics),
        overall_resistance_risk=overall_risk,
    )

    logger.info(f"✅ Resistance analysis complete for {pathogen} (patient {patient_id}): {overall_risk} risk, {len(resistance_markers)} markers")
    return result
