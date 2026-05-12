"""
TheraGenome AI — Treatment Comparison Engine
=============================================
Multi-drug comparison using existing pipeline.

Accepts a list of drugs and evaluates each through the router and
decision_engine, then ranks them deterministically based on:
- risk_level
- effectiveness (if available)
- toxicity
- confidence

Design
------
The comparator is a *stateless aggregator* that:
1. Does NOT duplicate model logic
2. REUSES router + decision_engine
3. DOES NOT filter by mode (ModeFilter handles that)
4. DOES NOT generate explanations (ExplainerEngine handles that)
5. Returns deterministic, structured comparison output
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.chatbot.intent_detector import Intent
from backend.chatbot.router import ModuleRouter
from backend.chatbot.decision_engine import DecisionEngine


# ──────────────────────────────────────────────
#  Scoring and ranking
# ──────────────────────────────────────────────

def _score_risk_level(risk_level: str) -> int:
    """
    Convert risk_level string to numeric score for ranking.
    
    Parameters
    ----------
    risk_level : str
        One of "low", "medium", "high", or "unknown".
    
    Returns
    -------
    int
        Numeric score where higher is better:
        - low = 3
        - medium = 2
        - high = 1
        - unknown = 0
    """
    risk_scores = {
        "low": 3,
        "medium": 2,
        "high": 1,
        "unknown": 0,
    }
    return risk_scores.get(risk_level.lower(), 0)


def _compute_drug_score(
    risk_level: str,
    confidence: float,
    effectiveness: float | None = None,
    toxicity: float | None = None,
) -> tuple[int, float]:
    """
    Compute a deterministic ranking score for a drug.
    
    Scoring hierarchy (in priority order):
    1. Risk level (low > medium > high)
    2. Effectiveness (if available)
    3. Toxicity (lower is better)
    4. Confidence (tie-breaker)
    
    Parameters
    ----------
    risk_level : str
        Clinical risk classification.
    confidence : float
        Decision confidence (0.0 – 1.0).
    effectiveness : float, optional
        Therapeutic effectiveness score. Higher is better.
    toxicity : float, optional
        Toxicity level. Lower is better.
    
    Returns
    -------
    tuple[int, float]
        (primary_score, tiebreaker_score) for deterministic ranking.
    """
    # Primary score: risk level (most important)
    primary = _score_risk_level(risk_level)
    
    # Tiebreaker score: weighted combination of effectiveness, toxicity, confidence
    # normalized to 0-1 range
    tiebreaker = confidence  # Confidence is primary tiebreaker
    
    if effectiveness is not None and effectiveness > 0:
        # Boost score if effectiveness is available
        tiebreaker = tiebreaker * 0.7 + (effectiveness / 100.0) * 0.3
    
    if toxicity is not None and toxicity > 0:
        # Penalize high toxicity
        tiebreaker = tiebreaker * 0.8 - (toxicity / 100.0) * 0.2
        tiebreaker = max(0.0, tiebreaker)  # Ensure non-negative
    
    return (primary, tiebreaker)


def _extract_effectiveness(result: dict[str, Any]) -> float | None:
    """
    Extract effectiveness score from a drug result.
    
    Parameters
    ----------
    result : dict
        Decision engine output for a single drug.
    
    Returns
    -------
    float or None
        Effectiveness score if available, else None.
    """
    variables = result.get("variables", {})
    
    # Try multiple possible sources
    if "effectiveness_score" in variables:
        return float(variables["effectiveness_score"])
    if "therapeutic_index" in variables:
        return float(variables["therapeutic_index"])
    if "efficacy" in variables:
        return float(variables["efficacy"])
    
    return None


def _extract_toxicity(result: dict[str, Any]) -> float | None:
    """
    Extract toxicity score from a drug result.
    
    Parameters
    ----------
    result : dict
        Decision engine output for a single drug.
    
    Returns
    -------
    float or None
        Toxicity score if available, else None.
    """
    variables = result.get("variables", {})
    
    # Try multiple possible sources
    if "toxicity_score" in variables:
        return float(variables["toxicity_score"])
    if "side_effect_score" in variables:
        return float(variables["side_effect_score"])
    
    return None


def _determine_decision_basis(
    best_drug: dict[str, Any],
    all_drugs: list[dict[str, Any]],
) -> list[str]:
    """
    Determine the machine-readable decision basis codes for ranking.
    
    Compares the best-ranked drug against the others to identify
    why it was ranked highest.
    
    Parameters
    ----------
    best_drug : dict
        The top-ranked drug result.
    all_drugs : list
        All compared drug results.
    
    Returns
    -------
    list[str]
        Decision basis codes (subset of allowed set).
    """
    if len(all_drugs) < 2:
        return []
    
    basis = []
    
    best_risk = _score_risk_level(best_drug.get("risk_level", "unknown"))
    best_confidence = best_drug.get("confidence", 0.0)
    
    # Check against other drugs
    others_with_lower_risk = [
        d for d in all_drugs
        if d != best_drug and _score_risk_level(d.get("risk_level", "unknown")) < best_risk
    ]
    
    if others_with_lower_risk:
        basis.append("LOWER_RISK")
    
    # Toxicity comparison
    best_toxicity = _extract_toxicity({"variables": best_drug})
    if best_toxicity is not None:
        others_with_higher_toxicity = [
            d for d in all_drugs
            if d != best_drug and (_extract_toxicity({"variables": d}) or 0) > best_toxicity
        ]
        if others_with_higher_toxicity:
            basis.append("LOWER_TOXICITY")
    
    # Effectiveness comparison
    best_effectiveness = _extract_effectiveness({"variables": best_drug})
    if best_effectiveness is not None:
        others_with_lower_effectiveness = [
            d for d in all_drugs
            if d != best_drug and (_extract_effectiveness({"variables": d}) or 0) < best_effectiveness
        ]
        if others_with_lower_effectiveness:
            basis.append("HIGHER_EFFECTIVENESS")
    
    # Confidence tiebreaker
    others_with_lower_confidence = [
        d for d in all_drugs
        if d != best_drug and d.get("confidence", 0.0) < best_confidence
    ]
    if others_with_lower_confidence:
        basis.append("HIGHER_CONFIDENCE")
    
    return basis


# ──────────────────────────────────────────────
#  Comparator engine
# ──────────────────────────────────────────────

class TreatmentComparator:
    """
    Stateless treatment comparison engine.
    
    Evaluates multiple drugs through the existing router + decision_engine
    pipeline and produces ranked comparison output.
    
    Usage::
    
        comparator = TreatmentComparator()
        result = comparator.compare(
            drugs=["drug_a", "drug_b"],
            context={"genetic_data": {...}, "infection_data": {...}}
        )
    """
    
    def __init__(self):
        """Initialize with router and decision engine instances."""
        self._router = ModuleRouter()
        self._decision_engine = DecisionEngine()
    
    def compare(
        self,
        drugs: list[str],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Compare multiple drugs using the existing pipeline.
        
        Parameters
        ----------
        drugs : list[str]
            Drug names to compare.
        context : dict, optional
            Shared context (genetic_data, infection_data, etc.).
        
        Returns
        -------
        dict
            Structured comparison result with schema:
            {
                "intent": "compare_drugs",
                "template": "DRUG_COMPARISON" or "INSUFFICIENT_DATA",
                "variables": {...},
                "comparison": [...],
                "ranking": [...],
                "summary": {...},
                "metadata": {...}
            }
        """
        context = context or {}
        
        # Validation: need at least 2 drugs
        if not drugs or len(drugs) < 2:
            return {
                "intent": "compare_drugs",
                "template": "INSUFFICIENT_DATA",
            }
        
        # Evaluate each drug through the pipeline
        drug_results: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        models_invoked: list[str] = []
        
        for drug in drugs[:4]:  # Cap at 4 to prevent abuse
            try:
                # Build context for this drug
                drug_context = {**context, "drug": drug}
                
                # Route through decision_engine for this drug
                route_result = self._router.route(Intent.DRUG_ANALYSIS, drug_context)
                
                if route_result.errors and not route_result.outputs:
                    errors.append({
                        "drug": drug,
                        "error": "pipeline_failed",
                        "details": route_result.errors,
                    })
                    continue
                
                # Get decision for this drug
                decision_result = self._decision_engine.evaluate(route_result)
                
                # Extract key fields for comparison
                drug_result = {
                    "drug": drug,
                    "risk_level": decision_result.get("variables", {}).get("risk_level", "unknown"),
                    "confidence": decision_result.get("variables", {}).get("confidence_score", 0.0),
                    "reason_codes": decision_result.get("explanation", {}).get("reason_codes", []),
                    "result": {
                        "risk_level": decision_result.get("variables", {}).get("risk_level", "unknown"),
                        "confidence": decision_result.get("variables", {}).get("confidence_score", 0.0),
                        "reason_codes": decision_result.get("explanation", {}).get("reason_codes", []),
                    },
                }
                
                drug_results.append(drug_result)
                models_invoked.extend(route_result.models_invoked)
                
            except Exception as exc:
                errors.append({
                    "drug": drug,
                    "error": "evaluation_failed",
                    "details": str(exc),
                })
        
        # Return error if no drugs were successfully evaluated
        if not drug_results:
            return {
                "intent": "compare_drugs",
                "template": "INSUFFICIENT_DATA",
            }
        
        # Rank drugs deterministically
        ranked = sorted(
            drug_results,
            key=lambda d: _compute_drug_score(
                risk_level=d["risk_level"],
                confidence=d["confidence"],
                effectiveness=_extract_effectiveness({"variables": d}),
                toxicity=_extract_toxicity({"variables": d}),
            ),
            reverse=True,
        )
        
        # Build ranking list (1-indexed)
        ranking = [
            {"drug": drug_result["drug"], "rank": idx + 1}
            for idx, drug_result in enumerate(ranked)
        ]
        
        # Build comparison list (preserve original order)
        comparison = [
            {
                "drug": dr["drug"],
                "result": dr["result"],
            }
            for dr in drug_results
        ]
        
        # Best option and decision basis
        best = ranked[0]
        decision_basis = _determine_decision_basis(best, drug_results)
        
        return {
            "intent": "compare_drugs",
            "template": "DRUG_COMPARISON",
            "variables": {
                "drugs": drugs,
            },
            "comparison": comparison,
            "ranking": ranking,
            "summary": {
                "best_option": best["drug"],
                "decision_basis": decision_basis,
            },
            "metadata": {
                "source": "comparator",
                "models_invoked": list(set(models_invoked)),  # Deduplicate
                "errors": errors if errors else None,
            },
        }
