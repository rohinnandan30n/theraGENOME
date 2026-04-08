"""
TheraGenome AI — Module Router
================================
Maps detected intents to the correct AI model pipeline(s) and
orchestrates execution in the right order.

Design
------
Each intent maps to a *routing plan* — an ordered list of model calls.
The router executes the plan and returns a unified ``RouteResult``
containing all model outputs, ready for the Decision Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.chatbot.intent_detector import Intent
from backend.models.genetic import genetic_analysis_model
from backend.models.resistance import antibiotic_resistance_model
from backend.models.toxicity import drug_toxicity_model


# ──────────────────────────────────────────────
#  Route result
# ──────────────────────────────────────────────

@dataclass
class RouteResult:
    """Aggregated outputs from all models invoked for an intent."""
    intent: Intent
    models_invoked: list[str] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.value,
            "models_invoked": self.models_invoked,
            "outputs": self.outputs,
            "errors": self.errors,
        }


# ──────────────────────────────────────────────
#  Therapy decision stub
# ──────────────────────────────────────────────

def therapy_decision_engine(
    genetic: dict[str, Any] | None = None,
    resistance: dict[str, Any] | None = None,
    toxicity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Combine upstream model outputs into a unified therapy recommendation.

    This is intentionally kept as a *simple aggregator* here.  The real
    decision logic lives in :pymod:`backend.chatbot.decision_engine`,
    which consumes the ``RouteResult`` after routing.  This stub exists
    so the router can attach a preliminary recommendation payload when
    multiple models are invoked together.
    """
    return {
        "preliminary_recommendation": True,
        "inputs_received": {
            "genetic": genetic is not None,
            "resistance": resistance is not None,
            "toxicity": toxicity is not None,
        },
        "status": "pending_decision_engine",
    }


# ──────────────────────────────────────────────
#  Router
# ──────────────────────────────────────────────

class ModuleRouter:
    """
    Routes an intent + context to the appropriate AI model(s).

    Usage::

        router = ModuleRouter()
        result = router.route(Intent.DRUG_ANALYSIS, context={...})
    """

    def route(self, intent: Intent, context: dict[str, Any] | None = None) -> RouteResult:
        """Dispatch *intent* to the correct model pipeline."""
        context = context or {}

        handler = self._DISPATCH.get(intent, self._handle_general_query)
        return handler(self, intent, context)

    # ─── intent handlers ──────────────────────

    def _handle_input_genetic_data(
        self, intent: Intent, context: dict[str, Any]
    ) -> RouteResult:
        result = RouteResult(intent=intent)
        try:
            genetic = genetic_analysis_model(context)
            result.models_invoked.append("genetic_analysis_model")
            result.outputs["genetic_analysis"] = genetic.to_dict()
        except Exception as exc:
            result.errors.append({"model": "genetic_analysis_model", "error": str(exc)})
        return result

    def _handle_input_infection_data(
        self, intent: Intent, context: dict[str, Any]
    ) -> RouteResult:
        result = RouteResult(intent=intent)
        try:
            resistance = antibiotic_resistance_model(context)
            result.models_invoked.append("antibiotic_resistance_model")
            result.outputs["resistance_analysis"] = resistance.to_dict()
        except Exception as exc:
            result.errors.append({"model": "antibiotic_resistance_model", "error": str(exc)})
        return result

    def _handle_drug_analysis(
        self, intent: Intent, context: dict[str, Any]
    ) -> RouteResult:
        result = RouteResult(intent=intent)

        drug = context.get("drug", "")

        # Toxicity screening
        try:
            tox = drug_toxicity_model(drug_name=drug, context=context)
            result.models_invoked.append("drug_toxicity_model")
            result.outputs["toxicity_analysis"] = tox.to_dict()
        except Exception as exc:
            result.errors.append({"model": "drug_toxicity_model", "error": str(exc)})

        # If genetic data is available, also run genetic analysis
        if context.get("genetic_data"):
            try:
                gen = genetic_analysis_model(context)
                result.models_invoked.append("genetic_analysis_model")
                result.outputs["genetic_analysis"] = gen.to_dict()
            except Exception as exc:
                result.errors.append({"model": "genetic_analysis_model", "error": str(exc)})

        # Preliminary therapy decision
        result.outputs["therapy_decision"] = therapy_decision_engine(
            genetic=result.outputs.get("genetic_analysis"),
            toxicity=result.outputs.get("toxicity_analysis"),
        )
        result.models_invoked.append("therapy_decision_engine")

        return result

    def _handle_compare_drugs(
        self, intent: Intent, context: dict[str, Any]
    ) -> RouteResult:
        result = RouteResult(intent=intent)
        drugs = context.get("drugs", [])

        if len(drugs) < 2:
            result.errors.append({
                "model": "drug_toxicity_model",
                "error": "comparison_requires_at_least_two_drugs",
            })
            return result

        comparisons: list[dict[str, Any]] = []
        for drug in drugs[:4]:  # cap at 4 to prevent abuse
            try:
                tox = drug_toxicity_model(drug_name=drug, context=context)
                comparisons.append(tox.to_dict())
                result.models_invoked.append(f"drug_toxicity_model({drug})")
            except Exception as exc:
                result.errors.append({"model": f"drug_toxicity_model({drug})", "error": str(exc)})

        result.outputs["drug_comparisons"] = comparisons
        return result

    def _handle_explain_result(
        self, intent: Intent, context: dict[str, Any]
    ) -> RouteResult:
        """
        Explain a previous result.  Requires ``result_id`` or ``result_data``
        in context so we know *what* to explain.
        """
        result = RouteResult(intent=intent)

        if not context.get("result_id") and not context.get("result_data"):
            result.errors.append({
                "model": "explain",
                "error": "no_result_reference_provided",
            })
        else:
            result.outputs["explanation_context"] = {
                "result_id": context.get("result_id"),
                "result_data": context.get("result_data"),
                "explanation_ready": True,
            }
            result.models_invoked.append("explanation_resolver")

        return result

    def _handle_general_query(
        self, intent: Intent, context: dict[str, Any]
    ) -> RouteResult:
        return RouteResult(
            intent=intent,
            models_invoked=["fallback_handler"],
            outputs={
                "message_code": "GENERAL_QUERY_RECEIVED",
                "supported_intents": [i.value for i in Intent],
            },
        )

    # ─── dispatch table ───────────────────────

    _DISPATCH: dict[Intent, Any] = {
        Intent.INPUT_GENETIC_DATA:   _handle_input_genetic_data,
        Intent.INPUT_INFECTION_DATA: _handle_input_infection_data,
        Intent.DRUG_ANALYSIS:        _handle_drug_analysis,
        Intent.COMPARE_DRUGS:        _handle_compare_drugs,
        Intent.EXPLAIN_RESULT:       _handle_explain_result,
        Intent.GENERAL_QUERY:        _handle_general_query,
    }
