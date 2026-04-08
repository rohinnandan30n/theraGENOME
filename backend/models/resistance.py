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

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


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

    Parameters
    ----------
    context : dict, optional
        Expected keys:
        - ``infection_data``: culture / sequencing results
        - ``pathogen``:       suspected or confirmed organism

    Returns
    -------
    ResistanceAnalysisResult
    """
    context = context or {}

    result = ResistanceAnalysisResult(
        pathogen_identified="Staphylococcus aureus (MRSA)",
        susceptibility_profile={
            "vancomycin": "susceptible",
            "linezolid": "susceptible",
            "daptomycin": "susceptible",
            "oxacillin": "resistant",
            "penicillin": "resistant",
            "erythromycin": "intermediate",
            "ciprofloxacin": "resistant",
        },
        resistance_markers=[
            asdict(ResistanceMarker(
                gene="mecA",
                mechanism="target_modification",
                antibiotic_class="beta_lactam",
                confidence=0.98,
            )),
            asdict(ResistanceMarker(
                gene="ermC",
                mechanism="target_modification",
                antibiotic_class="macrolide",
                confidence=0.85,
            )),
            asdict(ResistanceMarker(
                gene="norA",
                mechanism="efflux_pump",
                antibiotic_class="fluoroquinolone",
                confidence=0.91,
            )),
        ],
        recommended_antibiotics=["vancomycin", "linezolid", "daptomycin"],
        avoid_antibiotics=["oxacillin", "penicillin", "ciprofloxacin"],
        overall_resistance_risk="high",
    )

    return result
