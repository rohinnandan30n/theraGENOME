"""
TheraGenome AI — Demo Mode Engine
==================================
Provides pre-built demonstration scenarios that run through the full
chatbot pipeline without modifying core decision logic.

Each scenario:
- Contains pre-configured genetic, infection, and drug data
- Runs through process_query() for real pipeline execution
- Returns structured output for presentation/testing

Design
------
NO natural language generation
NO fake outputs
ONLY pre-configured data + real pipeline
Results are deterministic and repeatable
"""

from __future__ import annotations

from typing import Any
from backend.chatbot.controller import process_query
from backend.chatbot.templates import TemplateCode


# ──────────────────────────────────────────────
#  Demo Scenarios
# ──────────────────────────────────────────────

DEMO_SCENARIOS: dict[str, dict[str, Any]] = {
    "safe_case": {
        "id": "safe_case",
        "name": "Safe Treatment Case",
        "description": "Patient with no drug interactions; safe to use",
        "intent": "drug_analysis",
        "user_input": "Analyse drug toxicity and safety for amoxicillin",
        "context": {
            "drug": "amoxicillin",
            "genetic_data": {
                "patient_id": "DEMO_P001",
                "metabolizer_status": "normal_metabolizer",
                "variants": ["CYP2D6_normal", "CYP2C19_normal"],
            },
            "infection_data": {
                "pathogen": "Streptococcus pyogenes",
                "culture_date": "2025-12-01",
                "resistance_profile": {
                    "amoxicillin": "susceptible",
                    "cephalexin": "susceptible",
                },
            },
        },
    },
    "high_risk_case": {
        "id": "high_risk_case",
        "name": "High-Risk Case",
        "description": "Patient with genetic contraindications; requires caution",
        "intent": "drug_analysis",
        "user_input": "Evaluate medication safety for ciprofloxacin drug interaction risks",
        "context": {
            "drug": "ciprofloxacin",
            "genetic_data": {
                "patient_id": "DEMO_P002",
                "metabolizer_status": "poor_metabolizer",
                "variants": [
                    "CYP2D6_poor_metabolizer",
                    "HERG_cardiac_risk",
                    "LQT1_variant",
                ],
                "risk_alleles": ["HERG_mutation", "QT_prolongation_marker"],
            },
            "infection_data": {
                "pathogen": "Pseudomonas aeruginosa",
                "culture_date": "2025-12-01",
                "resistance_profile": {
                    "ciprofloxacin": "susceptible",
                    "tobramycin": "susceptible",
                    "carbapenems": "susceptible",
                },
            },
        },
    },
    "comparison_case": {
        "id": "comparison_case",
        "name": "Multi-Drug Comparison",
        "description": "Compare efficacy and safety of two antibiotics",
        "intent": "compare_drugs",
        "user_input": "Compare and contrast vancomycin versus linezolid for treatment",
        "context": {
            "drugs": ["vancomycin", "linezolid"],
            "genetic_data": {
                "patient_id": "DEMO_P003",
                "metabolizer_status": "normal_metabolizer",
                "variants": ["CYP2D6_normal", "CYP2C19_normal"],
                "renal_function": "normal",
                "hepatic_function": "normal",
            },
            "infection_data": {
                "pathogen": "Staphylococcus aureus (MRSA)",
                "culture_date": "2025-12-01",
                "resistance_profile": {
                    "vancomycin": "susceptible",
                    "linezolid": "susceptible",
                    "oxacillin": "resistant",
                    "penicillin": "resistant",
                },
            },
        },
    },
}


# ──────────────────────────────────────────────
#  Demo Engine Functions
# ──────────────────────────────────────────────

def get_demo_cases() -> list[dict[str, Any]]:
    """
    Return list of available demo scenarios.

    Returns
    -------
    list[dict]
        Each dict contains:
        - ``id``: scenario identifier
        - ``name``: display name
        - ``description``: brief explanation
        - ``intent``: detected intent
    """
    return [
        {
            "id": case.get("id"),
            "name": case.get("name"),
            "description": case.get("description"),
            "intent": case.get("intent"),
        }
        for case in DEMO_SCENARIOS.values()
    ]


def run_demo_case(
    case_id: str,
    mode: str = "doctor",
    scope: str = "full",
) -> dict[str, Any]:
    """
    Execute a pre-configured demo scenario through the pipeline.

    This function:
    1. Loads the scenario by ID
    2. Passes input through process_query()
    3. Wraps output with demo metadata

    Parameters
    ----------
    case_id : str
        Identifier of demo scenario (from ``get_demo_cases()``)
    mode : str, optional
        ``"doctor"`` or ``"patient"`` display mode
    scope : str, optional
        ``"full"`` or ``"summary"`` explanation scope

    Returns
    -------
    dict
        Wrapped response with structure::

            {
                "intent": "demo_run",
                "template": "DEMO_RESULT",
                "scenario": {
                    "id": "...",
                    "name": "...",
                    "description": "..."
                },
                "result": {
                    # Full process_query() response
                },
                "metadata": {
                    "source": "demo_engine",
                    "scenario_id": "...",
                    "mode": "...",
                    "scope": "..."
                }
            }

    Raises
    ------
    ValueError
        If case_id is not found in DEMO_SCENARIOS
    """
    if case_id not in DEMO_SCENARIOS:
        available = list(DEMO_SCENARIOS.keys())
        raise ValueError(
            f"Unknown demo case: {case_id!r}. "
            f"Available: {available}"
        )

    scenario = DEMO_SCENARIOS[case_id]

    # Run through full pipeline
    result = process_query(
        user_input=scenario["user_input"],
        mode=mode,
        context=scenario["context"],
        scope=scope,
    )

    # Wrap with demo metadata
    return {
        "intent": "demo_run",
        "template": TemplateCode.DEMO_RESULT.value,
        "scenario": {
            "id": scenario["id"],
            "name": scenario["name"],
            "description": scenario["description"],
        },
        "result": result,
        "metadata": {
            "source": "demo_engine",
            "scenario_id": case_id,
            "mode": mode,
            "scope": scope,
        },
    }


def run_all_demo_cases(
    mode: str = "doctor",
    scope: str = "full",
) -> list[dict[str, Any]]:
    """
    Execute all demo scenarios and return results.

    Useful for batch testing and validation.

    Parameters
    ----------
    mode : str, optional
        Display mode (``"doctor"`` or ``"patient"``)
    scope : str, optional
        Explanation scope (``"full"`` or ``"summary"``)

    Returns
    -------
    list[dict]
        List of demo results (one per scenario)
    """
    results = []
    for case_id in DEMO_SCENARIOS.keys():
        try:
            demo_result = run_demo_case(case_id=case_id, mode=mode, scope=scope)
            results.append(demo_result)
        except Exception as e:
            results.append({
                "intent": "demo_run",
                "template": TemplateCode.DEMO_RESULT.value,
                "scenario": {
                    "id": case_id,
                    "name": DEMO_SCENARIOS[case_id]["name"],
                },
                "error": str(e),
                "metadata": {
                    "source": "demo_engine",
                    "scenario_id": case_id,
            "mode": mode,
                },
            })
    return results
