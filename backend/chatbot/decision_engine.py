"""
TheraGenome AI — Decision Engine
==================================
Consumes aggregated model outputs from the router and produces the
final clinical-decision payload:

- ``risk_level``       — low / medium / high
- ``recommended_drug`` — best candidate (or null)
- ``confidence_score`` — 0.0 – 1.0
- ``reason_codes``     — machine-readable rationale array

The engine also selects the correct response template.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.chatbot.intent_detector import Intent
from backend.chatbot.router import RouteResult
from backend.chatbot.templates import TemplateCode, build_response


# ──────────────────────────────────────────────
#  Decision payload
# ──────────────────────────────────────────────

@dataclass
class Decision:
    """Output of the decision engine before template rendering."""
    risk_level: str = "unknown"         # low | medium | high
    recommended_drug: str | None = None
    confidence_score: float = 0.0       # 0.0 – 1.0
    reason_codes: list[str] = field(default_factory=list)
    reason_details: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "recommended_drug": self.recommended_drug,
            "confidence_score": round(self.confidence_score, 4),
            "reason_codes": self.reason_codes,
        }


# ──────────────────────────────────────────────
#  Engine
# ──────────────────────────────────────────────

class DecisionEngine:
    """
    Stateless decision engine.

    Call :py:meth:`evaluate` with a ``RouteResult`` to get the final
    structured response ready for the API layer.
    """

    def evaluate(
        self,
        route_result: RouteResult,
    ) -> dict[str, Any]:
        """
        Produce the final chatbot response.

        Parameters
        ----------
        route_result : RouteResult
            Aggregated model outputs from the router.
        mode : str
            ``"doctor"`` or ``"patient"`` — controls detail level.

        Returns
        -------
        dict
            JSON-serialisable response envelope (see ``templates.build_response``).
        """
        intent = route_result.intent

        # Short-circuit: if the router reported errors and no outputs,
        # we need more data.
        if route_result.errors and not route_result.outputs:
            return self._require_more_data(route_result)

        handler = self._HANDLERS.get(intent, self._handle_general)
        return handler(self, route_result)

    # ─── Per-intent decision logic ────────────

    def _handle_drug_analysis(
        self, rr: RouteResult
    ) -> dict[str, Any]:
        tox = rr.outputs.get("toxicity_analysis", {})
        gen = rr.outputs.get("genetic_analysis", {})

        decision = self._compute_drug_decision(tox, gen)
        template = self._select_drug_template(decision)

        variables: dict[str, Any] = {
            "drug_name": tox.get("drug_name", "unknown"),
            "risk_level": decision.risk_level,
            "recommended_drug": decision.recommended_drug,
            "confidence_score": decision.confidence_score,
            "reason_codes": decision.reason_codes,
        }

        return build_response(
            intent=rr.intent.value,
            template=template,
            variables=variables,
            reason_codes=decision.reason_codes,
            reason_details=decision.reason_details,
            modules=rr.outputs,
            metadata={"models_invoked": rr.models_invoked},
        )

    def _handle_compare_drugs(
        self, rr: RouteResult
    ) -> dict[str, Any]:
        comparisons = rr.outputs.get("drug_comparisons", [])

        if not comparisons:
            return self._require_more_data(rr)

        # Rank by therapeutic index (higher = safer)
        ranked = sorted(comparisons, key=lambda d: d.get("therapeutic_index", 0), reverse=True)
        best = ranked[0]

        decision = Decision(
            risk_level=best.get("overall_toxicity_risk", "unknown"),
            recommended_drug=best.get("drug_name"),
            confidence_score=min(0.99, best.get("therapeutic_index", 0) / 10),
            reason_codes=["highest_therapeutic_index", "lowest_relative_toxicity"],
            reason_details=[
                {"code": "HIGHEST_THERAPEUTIC_INDEX", "module": "comparison", "severity": "low"},
                {"code": "LOWEST_RELATIVE_TOXICITY", "module": "comparison", "severity": "low"}
            ]
        )

        variables: dict[str, Any] = {
            "drugs_compared": [d.get("drug_name") for d in comparisons],
            "recommended_drug": decision.recommended_drug,
            "risk_level": decision.risk_level,
            "confidence_score": decision.confidence_score,
            "reason_codes": decision.reason_codes,
        }

        return build_response(
            intent=rr.intent.value,
            template=TemplateCode.COMPARISON_RESULT,
            variables=variables,
            reason_codes=decision.reason_codes,
            reason_details=decision.reason_details,
            modules=rr.outputs,
            metadata={"models_invoked": rr.models_invoked},
        )

    def _handle_input_genetic_data(
        self, rr: RouteResult
    ) -> dict[str, Any]:
        gen = rr.outputs.get("genetic_analysis", {})

        decision = Decision(
            risk_level=gen.get("overall_genetic_risk", "unknown"),
            recommended_drug=None,
            confidence_score=0.90 if gen else 0.0,
            reason_codes=["genetic_profile_processed"],
            reason_details=[
                {"code": "GENETIC_PROFILE_PROCESSED", "module": "genetic", "severity": "info"}
            ]
        )

        variables: dict[str, Any] = {
            "metabolizer_status": gen.get("patient_metabolizer_status"),
            "risk_alleles_count": len(gen.get("risk_alleles", [])),
            "risk_level": decision.risk_level,
            "reason_codes": decision.reason_codes,
        }

        return build_response(
            intent=rr.intent.value,
            template=TemplateCode.GENETIC_DATA_RECEIVED,
            variables=variables,
            reason_codes=decision.reason_codes,
            reason_details=decision.reason_details,
            modules=rr.outputs,
            metadata={"models_invoked": rr.models_invoked},
        )

    def _handle_input_infection_data(
        self, rr: RouteResult
    ) -> dict[str, Any]:
        res = rr.outputs.get("resistance_analysis", {})

        recommended = res.get("recommended_antibiotics", [])
        decision = Decision(
            risk_level=res.get("overall_resistance_risk", "unknown"),
            recommended_drug=recommended[0] if recommended else None,
            confidence_score=0.88 if res else 0.0,
            reason_codes=["resistance_profile_processed", "susceptibility_tested"],
            reason_details=[
                {"code": "RESISTANCE_PROFILE_PROCESSED", "module": "resistance", "severity": "info"},
                {"code": "SUSCEPTIBILITY_TESTED", "module": "resistance", "severity": "info"}
            ]
        )

        variables: dict[str, Any] = {
            "pathogen": res.get("pathogen_identified"),
            "recommended_antibiotics": recommended,
            "avoid_antibiotics": res.get("avoid_antibiotics", []),
            "risk_level": decision.risk_level,
            "reason_codes": decision.reason_codes,
        }

        return build_response(
            intent=rr.intent.value,
            template=TemplateCode.INFECTION_DATA_RECEIVED,
            variables=variables,
            reason_codes=decision.reason_codes,
            reason_details=decision.reason_details,
            modules=rr.outputs,
            metadata={"models_invoked": rr.models_invoked},
        )

    def _handle_general(
        self, rr: RouteResult
    ) -> dict[str, Any]:
        return build_response(
            intent=rr.intent.value,
            template=TemplateCode.GENERAL_RESPONSE,
            variables={"supported_intents": rr.outputs.get("supported_intents", [])},
            reason_codes=["general_query_processed"],
            reason_details=[{"code": "GENERAL_QUERY_PROCESSED", "module": "general", "severity": "info"}],
            modules=rr.outputs,
            metadata={"models_invoked": rr.models_invoked},
        )

    # ─── helpers ──────────────────────────────

    def _require_more_data(self, rr: RouteResult) -> dict[str, Any]:
        return build_response(
            intent=rr.intent.value,
            template=TemplateCode.REQUIRE_MORE_DATA,
            variables={
                "errors": rr.errors,
                "missing_fields": self._infer_missing_fields(rr),
            },
            reason_codes=["insufficient_data"],
            reason_details=[{"code": "INSUFFICIENT_DATA", "module": "router", "severity": "high"}],
            modules={},
            metadata={"models_invoked": rr.models_invoked},
        )

    @staticmethod
    def _infer_missing_fields(rr: RouteResult) -> list[str]:
        """Derive a list of missing input fields from error messages."""
        missing: list[str] = []
        for err in rr.errors:
            msg = err.get("error", "")
            if "two_drugs" in msg or "comparison" in msg:
                missing.append("drugs")
            elif "result_reference" in msg:
                missing.append("result_id")
            else:
                missing.append("context_data")
        return missing

    @staticmethod
    def _compute_drug_decision(
        tox: dict[str, Any],
        gen: dict[str, Any],
    ) -> Decision:
        """Combine toxicity + genetic signals into a single decision."""
        tox_risk = tox.get("overall_toxicity_risk", "unknown")
        gen_risk = gen.get("overall_genetic_risk", "unknown")

        # Risk escalation matrix
        risk_rank = {"low": 0, "medium": 1, "high": 2, "unknown": 1}
        combined = max(risk_rank.get(tox_risk, 1), risk_rank.get(gen_risk, 1))
        risk_map = {0: "low", 1: "medium", 2: "high"}
        risk_level = risk_map[combined]

        # Confidence: start high, penalise for risk signals
        confidence = 0.92
        reason_codes: list[str] = []
        reason_details: list[dict[str, str]] = []

        if tox_risk == "high":
            confidence -= 0.25
            reason_codes.append("high_toxicity_risk")
            reason_details.append({"code": "HIGH_TOXICITY_RISK", "module": "toxicity", "severity": "high"})
        elif tox_risk == "medium":
            confidence -= 0.10
            reason_codes.append("moderate_toxicity_risk")
            reason_details.append({"code": "MODERATE_TOXICITY_RISK", "module": "toxicity", "severity": "medium"})

        if gen_risk == "high":
            confidence -= 0.20
            reason_codes.append("adverse_genetic_profile")
            reason_details.append({"code": "ADVERSE_GENETIC_PROFILE", "module": "genetic", "severity": "high"})
        elif gen_risk == "medium":
            confidence -= 0.08
            reason_codes.append("genetic_caution_advised")
            reason_details.append({"code": "GENETIC_CAUTION_ADVISED", "module": "genetic", "severity": "medium"})

        if tox.get("contraindications"):
            confidence -= 0.15
            reason_codes.append("contraindications_present")
            reason_details.append({"code": "CONTRAINDICATIONS_PRESENT", "module": "toxicity", "severity": "high"})

        if not reason_codes:
            reason_codes.append("no_significant_risks_detected")
            reason_details.append({"code": "NO_SIGNIFICANT_RISKS_DETECTED", "module": "system", "severity": "low"})

        confidence = max(0.0, min(1.0, confidence))

        # Drug recommendation
        drug_name = tox.get("drug_name", "unknown")
        recommended = drug_name if risk_level != "high" else None

        return Decision(
            risk_level=risk_level,
            recommended_drug=recommended,
            confidence_score=confidence,
            reason_codes=reason_codes,
            reason_details=reason_details,
        )

    @staticmethod
    def _select_drug_template(decision: Decision) -> TemplateCode:
        if decision.risk_level == "high":
            return TemplateCode.DRUG_NOT_RECOMMENDED
        if decision.risk_level == "medium":
            return TemplateCode.DRUG_USE_WITH_CAUTION
        return TemplateCode.SAFE_TO_USE

    # ─── dispatch table ───────────────────────

    _HANDLERS: dict[Intent, Any] = {
        Intent.DRUG_ANALYSIS:        _handle_drug_analysis,
        Intent.COMPARE_DRUGS:        _handle_compare_drugs,
        Intent.INPUT_GENETIC_DATA:   _handle_input_genetic_data,
        Intent.INPUT_INFECTION_DATA: _handle_input_infection_data,
        Intent.GENERAL_QUERY:        _handle_general,
    }
