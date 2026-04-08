"""
TheraGenome AI — Test Suite
============================
Three required test scenarios:

1. drug_analysis        — full pipeline, validates template + risk
2. compare_drugs        — multi-drug comparison, checks ranking
3. missing_data         — ensures REQUIRE_MORE_DATA when context is empty

Run with::

    pytest backend/tests/ -v
"""

from __future__ import annotations

import sys
import os
from typing import Any

# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.chatbot.controller import process_query
from backend.chatbot.intent_detector import IntentDetector, Intent
from backend.chatbot.templates import TemplateCode


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _assert_envelope(resp: dict) -> None:
    """Every response must have the canonical envelope keys."""
    for key in ("intent", "template", "variables", "metadata"):
        assert key in resp, f"Missing key: {key}"
    
    if resp["intent"] == "input_guidance":
        assert "guidance" in resp
    elif resp["intent"] == "safety_guardrail":
        assert "safety" in resp
    else:
        assert "explanation" in resp, "Missing key: explanation"
        assert "reason_codes" in resp["explanation"]
        assert "reason_details" in resp["explanation"]
    
    # Error/special responses don't need linked_response_id
    error_templates = {
        TemplateCode.INSUFFICIENT_CONTEXT.value,
        TemplateCode.REQUIRE_MORE_DATA.value,
        TemplateCode.REQUEST_MISSING_INFO.value,
    }
    if resp["intent"] not in ("input_guidance", "safety_guardrail") and resp["template"] not in error_templates:
        assert "linked_response_id" in resp["metadata"]

    assert resp["template"] in [t.value for t in TemplateCode], f"Unknown template: {resp['template']}"


# ──────────────────────────────────────────────
#  1. Drug analysis — full pipeline
# ──────────────────────────────────────────────

class TestDrugAnalysis:
    """Validates the drug_analysis intent end-to-end."""

    def test_intent_detected(self) -> None:
        detector = IntentDetector()
        result = detector.detect("What is the toxicity of amoxicillin?")
        assert result.intent == Intent.DRUG_ANALYSIS
        assert result.confidence >= 0.80

    def test_full_pipeline_doctor_mode(self) -> None:
        resp = process_query(
            user_input="Analyse drug toxicity for ciprofloxacin",
            mode="doctor",
            context={"drug": "ciprofloxacin", "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},
        )
        _assert_envelope(resp)

        assert resp["intent"] == "drug_analysis"
        assert resp["template"] in (
            TemplateCode.DRUG_NOT_RECOMMENDED.value,
            TemplateCode.DRUG_USE_WITH_CAUTION.value,
            TemplateCode.SAFE_TO_USE.value,
        )
        assert "drug_name" in resp["variables"]
        assert "risk_level" in resp["variables"]
        assert resp["variables"]["risk_level"] in ("low", "medium", "high")

        # Doctor mode includes full model output
        assert "toxicity_analysis" in resp["explanation"]["modules"]

    def test_full_pipeline_patient_mode(self) -> None:
        resp = process_query(
            user_input="Is this drug safe?",
            mode="patient",
            context={"drug": "metformin", "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},
        )
        _assert_envelope(resp)
        assert resp["intent"] == "drug_analysis"
        # Patient mode should NOT expose raw model output
        assert "modules" not in resp["explanation"]
        assert "reason_codes" in resp["explanation"]

    def test_confidence_score_range(self) -> None:
        resp = process_query(
            user_input="Drug interaction check",
            mode="doctor",
            context={"drug": "warfarin", "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},
        )
        score = resp["variables"].get("confidence_score", -1)
        assert 0.0 <= score <= 1.0

    def test_reason_codes_present(self) -> None:
        resp = process_query(
            user_input="Evaluate drug side effects",
            mode="doctor",
            context={"drug": "aspirin", "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},
        )
        codes = resp["variables"].get("reason_codes", [])
        assert isinstance(codes, list)
        assert len(codes) > 0


# ──────────────────────────────────────────────
#  2. Compare drugs
# ──────────────────────────────────────────────

class TestCompareDrugs:
    """Validates the compare_drugs intent end-to-end."""

    def test_intent_detected(self) -> None:
        detector = IntentDetector()
        result = detector.detect("Compare penicillin versus vancomycin")
        assert result.intent == Intent.COMPARE_DRUGS
        assert result.confidence >= 0.75

    def test_comparison_result(self) -> None:
        resp = process_query(
            user_input="Which drug is better: amoxicillin vs doxycycline?",
            mode="doctor",
            context={"drugs": ["amoxicillin", "doxycycline"], "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},
        )
        _assert_envelope(resp)

        assert resp["intent"] == "compare_drugs"
        assert resp["template"] == TemplateCode.COMPARISON_RESULT.value
        assert "drugs_compared" in resp["variables"]
        assert "recommended_drug" in resp["variables"]
        assert len(resp["variables"]["drugs_compared"]) == 2

    def test_comparison_patient_mode(self) -> None:
        resp = process_query(
            user_input="Compare these two medicines",
            mode="patient",
            context={"drugs": ["drugA", "drugB"], "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},
        )
        _assert_envelope(resp)
        # Patient mode hides raw model outputs
        assert "modules" not in resp["explanation"]


# ──────────────────────────────────────────────
#  3. Missing data scenario
# ──────────────────────────────────────────────

class TestMissingData:
    """Validates graceful handling when required context is missing."""

    def test_compare_without_drugs(self) -> None:
        """compare_drugs with no drugs list → REQUIRE_MORE_DATA."""
        resp = process_query(
            user_input="Compare these medications",
            mode="doctor",
            context={},  # no "drugs" key
        )
        _assert_envelope(resp)
        assert resp["template"] == TemplateCode.REQUIRE_MORE_DATA.value
        assert "errors" in resp["variables"]
        assert "missing_fields" in resp["variables"]

    def test_explain_without_reference(self) -> None:
        """explain_result with no last_response → INSUFFICIENT_CONTEXT."""
        resp = process_query(
            user_input="Explain this result to me",
            mode="doctor",
            context={},  # no last_response
        )
        _assert_envelope(resp)
        assert resp["template"] == TemplateCode.INSUFFICIENT_CONTEXT.value

    def test_empty_input(self) -> None:
        """Empty string → general_query with low confidence."""
        resp = process_query(user_input="", mode="doctor")
        _assert_envelope(resp)
        assert resp["intent"] == "general_query"
        assert resp["metadata"]["intent_confidence"] <= 0.40

    def test_unknown_query(self) -> None:
        """Completely unrelated text → general_query fallback."""
        resp = process_query(
            user_input="What's the weather like today?",
            mode="doctor",
        )
        _assert_envelope(resp)
        assert resp["intent"] == "general_query"
        assert resp["template"] == TemplateCode.GENERAL_RESPONSE.value


# ──────────────────────────────────────────────
#  4. Additional edge cases
# ──────────────────────────────────────────────

class TestEdgeCases:
    """Extra coverage for robustness."""

    def test_genetic_data_intent(self) -> None:
        resp = process_query(
            user_input="Here is my DNA genome sequencing data",
            mode="doctor",
            context={"genetic_data": {"markers": ["CYP2D6"]}, "infection_data": {"a":"b"}},
        )
        _assert_envelope(resp)
        assert resp["intent"] == "input_genetic_data"
        assert resp["template"] == TemplateCode.GENETIC_DATA_RECEIVED.value

    def test_infection_data_intent(self) -> None:
        resp = process_query(
            user_input="Patient has MRSA infection culture results",
            mode="doctor",
            context={"infection_data": {"pathogen": "MRSA"}, "genetic_data": {"x":"y"}},
        )
        _assert_envelope(resp)
        assert resp["intent"] == "input_infection_data"
        assert resp["template"] == TemplateCode.INFECTION_DATA_RECEIVED.value

    def test_metadata_always_present(self) -> None:
        resp = process_query(user_input="hello", mode="doctor")
        meta = resp["metadata"]
        assert "processing_time_ms" in meta
        assert "intent_confidence" in meta
        assert meta["processing_time_ms"] >= 0

    def test_no_natural_language_in_response(self) -> None:
        """Responses must NEVER contain human-readable sentences as values."""
        resp = process_query(
            user_input="Check amoxicillin",
            mode="doctor",
            context={"drug": "amoxicillin"},
        )
        # The template value must be an uppercase code, not a sentence
        assert resp["template"] == resp["template"].upper()
        assert " " not in resp["template"]  # no spaces = not a sentence

    def test_mode_consistency(self) -> None:
        """Verifies that doctor and patient modes are identical except for explanation detail."""
        query = "Analyse drug toxicity for ciprofloxacin"
        ctx = {"drug": "ciprofloxacin", "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}}

        resp_doc = process_query(query, mode="doctor", context=ctx)
        resp_pat = process_query(query, mode="patient", context=ctx)

        _assert_envelope(resp_doc)
        _assert_envelope(resp_pat)

        # Core engine outputs MUST be identical
        assert resp_doc["template"] == resp_pat["template"]
        assert resp_doc["variables"] == resp_pat["variables"]
        assert resp_doc["explanation"]["reason_codes"] == resp_pat["explanation"]["reason_codes"]

        # Only the output detail level should differ
        assert "modules" in resp_doc["explanation"]
        assert "modules" not in resp_pat["explanation"]
        assert resp_doc["metadata"]["mode"] == "doctor"
        assert resp_pat["metadata"]["mode"] == "patient"


# ──────────────────────────────────────────────
#  5. Explain Result
# ──────────────────────────────────────────────

class TestExplainer:
    """Validates the ExplainerEngine integration."""

    def test_explainer_with_context_doctor(self) -> None:
        last_resp = {
            "intent": "drug_analysis",
            "template": TemplateCode.DRUG_NOT_RECOMMENDED.value,
            "variables": {},
            "explanation": {
                "reason_codes": ["high_toxicity", "contraindicated"],
                "reason_details": [{"code": "HIGH_TOXICITY", "module": "toxicity", "severity": "high"}],
                "modules": {"toxicity_analysis": {"score": 0.9}}
            },
            "metadata": {"linked_response_id": "test-id"}
        }
        resp = process_query(
            "Why did you recommend this?",
            mode="doctor",
            context={"last_response": last_resp}
        )
        
        _assert_envelope(resp)
        assert resp["intent"] == "explain_result"
        assert resp["template"] == TemplateCode.EXPLANATION_SUMMARY.value
        assert resp["explanation"]["reason_codes"] == ["high_toxicity", "contraindicated"]
        assert "toxicity_analysis" in resp["explanation"]["modules"]
        
    def test_explainer_with_context_patient(self) -> None:
        last_resp = {
            "intent": "drug_analysis",
            "template": TemplateCode.DRUG_NOT_RECOMMENDED.value,
            "variables": {},
            "explanation": {
                "reason_codes": ["high_toxicity"],
                "reason_details": [],
                "modules": {"toxicity_analysis": {"score": 0.9}}
            },
            "metadata": {"linked_response_id": "test-id"}
        }
        resp = process_query(
            "Please explain why?",
            mode="patient",
            context={"last_response": last_resp}
        )
        
        _assert_envelope(resp)
        assert resp["intent"] == "explain_result"
        assert resp["explanation"]["reason_codes"] == ["high_toxicity"]
        # Patient mode should strip modules
        assert "modules" not in resp["explanation"]

    def test_explainer_with_scope(self) -> None:
        last_resp = {
            "intent": "drug_analysis",
            "template": TemplateCode.DRUG_NOT_RECOMMENDED.value,
            "variables": {},
            "explanation": {
                "reason_codes": ["high_toxicity", "adverse_genetic"],
                "reason_details": [],
                "modules": {
                    "toxicity_analysis": {"score": 0.9},
                    "genetic_analysis": {"score": 0.8}
                }
            },
            "metadata": {"linked_response_id": "test-id"}
        }
        resp = process_query(
            "Why?",
            mode="doctor",
            context={"last_response": last_resp},
            scope="toxicity"
        )
        _assert_envelope(resp)
        assert resp["variables"]["scope"] == "toxicity"
        assert "toxicity_analysis" in resp["explanation"]["modules"]
        assert "genetic_analysis" not in resp["explanation"]["modules"]
        
    def test_explainer_missing_context(self) -> None:
        resp = process_query(
            "Why?",
            mode="doctor",
            context={}  # Missing last_response
        )
        
        _assert_envelope(resp)
        assert resp["intent"] == "explain_result"
        assert resp["template"] == TemplateCode.INSUFFICIENT_CONTEXT.value
        assert "INSUFFICIENT_DATA" in resp["explanation"]["reason_codes"]


# ──────────────────────────────────────────────
#  6. Treatment Comparator Tests
# ──────────────────────────────────────────────

class TestTreatmentComparator:
    """Validates the TreatmentComparator module."""

    def test_comparator_import(self) -> None:
        """Verify comparator module can be imported."""
        from backend.chatbot.comparator import TreatmentComparator
        comp = TreatmentComparator()
        assert comp is not None

    def test_compare_two_drugs(self) -> None:
        """Compare exactly 2 drugs — should rank them."""
        from backend.chatbot.comparator import TreatmentComparator
        comp = TreatmentComparator()
        
        result = comp.compare(
            drugs=["amoxicillin", "doxycycline"],
            context={},
        )
        
        assert result["intent"] == "compare_drugs"
        assert result["template"] == "DRUG_COMPARISON"
        assert len(result["comparison"]) == 2
        assert len(result["ranking"]) == 2
        assert "best_option" in result["summary"]
        assert "decision_basis" in result["summary"]
        
        # Ranking should be 1-indexed
        ranks = [r["rank"] for r in result["ranking"]]
        assert set(ranks) == {1, 2}

    def test_compare_three_drugs(self) -> None:
        """Compare 3 drugs — should rank all three."""
        from backend.chatbot.comparator import TreatmentComparator
        comp = TreatmentComparator()
        
        result = comp.compare(
            drugs=["cephalexin", "ciprofloxacin", "clarithromycin"],
            context={},
        )
        
        assert result["intent"] == "compare_drugs"
        assert result["template"] == "DRUG_COMPARISON"
        assert len(result["comparison"]) == 3
        assert len(result["ranking"]) == 3
        
        # All drugs should be represented in ranking with ranks 1, 2, 3
        ranks = sorted([r["rank"] for r in result["ranking"]])
        assert ranks == [1, 2, 3]

    def test_compare_insufficient_drugs(self) -> None:
        """Less than 2 drugs → INSUFFICIENT_DATA."""
        from backend.chatbot.comparator import TreatmentComparator
        comp = TreatmentComparator()
        
        result = comp.compare(drugs=["single_drug"], context={})
        assert result["intent"] == "compare_drugs"
        assert result["template"] == "INSUFFICIENT_DATA"
        
        result_empty = comp.compare(drugs=[], context={})
        assert result_empty["template"] == "INSUFFICIENT_DATA"

    def test_comparison_structure(self) -> None:
        """Verify the comparison output structure matches requirements."""
        from backend.chatbot.comparator import TreatmentComparator
        comp = TreatmentComparator()
        
        result = comp.compare(
            drugs=["drugA", "drugB"],
            context={},
        )
        
        # Required top-level keys
        assert "intent" in result
        assert "template" in result
        assert "variables" in result
        assert "comparison" in result
        assert "ranking" in result
        assert "summary" in result
        assert "metadata" in result
        
        # Comparison items
        for item in result["comparison"]:
            assert "drug" in item
            assert "result" in item
            assert "risk_level" in item["result"]
            assert "confidence" in item["result"]
            assert "reason_codes" in item["result"]
        
        # Ranking items
        for item in result["ranking"]:
            assert "drug" in item
            assert "rank" in item
            assert isinstance(item["rank"], int)
        
        # Summary
        summary = result["summary"]
        assert "best_option" in summary
        assert "decision_basis" in summary
        assert isinstance(summary["decision_basis"], list)


# ──────────────────────────────────────────────
#  7. Demo Mode Engine
# ──────────────────────────────────────────────

class TestDemoEngine:
    """Validates the demo mode engine and pre-configured scenarios."""

    def test_demo_import(self) -> None:
        """Demo module can be imported."""
        from backend.chatbot.demo import get_demo_cases, run_demo_case
        assert callable(get_demo_cases)
        assert callable(run_demo_case)

    def test_get_demo_cases_returns_list(self) -> None:
        """get_demo_cases() returns list of available scenarios."""
        from backend.chatbot.demo import get_demo_cases
        cases = get_demo_cases()
        
        assert isinstance(cases, list)
        assert len(cases) >= 3, "Must have at least 3 demo scenarios"

    def test_demo_cases_have_required_fields(self) -> None:
        """Each demo case has id, name, description, and intent."""
        from backend.chatbot.demo import get_demo_cases
        cases = get_demo_cases()
        
        for case in cases:
            assert "id" in case
            assert "name" in case
            assert "description" in case
            assert "intent" in case
            assert isinstance(case["id"], str)
            assert len(case["id"]) > 0

    def test_run_demo_safe_case(self) -> None:
        """Run safe_case scenario through pipeline."""
        from backend.chatbot.demo import run_demo_case
        result = run_demo_case(case_id="safe_case")
        
        assert result["intent"] == "demo_run"
        assert result["template"] == TemplateCode.DEMO_RESULT.value
        assert "scenario" in result
        assert "result" in result
        assert "metadata" in result
        
        # Verify scenario metadata
        scenario = result["scenario"]
        assert scenario["id"] == "safe_case"
        assert "name" in scenario
        assert "description" in scenario
        
        # Verify inner result is a valid response
        inner = result["result"]
        _assert_envelope(inner)
        assert inner["intent"] == "drug_analysis"

    def test_run_demo_high_risk_case(self) -> None:
        """Run high_risk_case scenario through pipeline."""
        from backend.chatbot.demo import run_demo_case
        result = run_demo_case(case_id="high_risk_case")
        
        assert result["intent"] == "demo_run"
        assert result["template"] == TemplateCode.DEMO_RESULT.value
        assert result["scenario"]["id"] == "high_risk_case"
        
        # Inner response must be valid
        inner = result["result"]
        _assert_envelope(inner)
        assert inner["intent"] == "drug_analysis"

    def test_run_demo_comparison_case(self) -> None:
        """Run comparison_case scenario through pipeline."""
        from backend.chatbot.demo import run_demo_case
        result = run_demo_case(case_id="comparison_case")
        
        assert result["intent"] == "demo_run"
        assert result["template"] == TemplateCode.DEMO_RESULT.value
        assert result["scenario"]["id"] == "comparison_case"
        
        # Inner response must be valid
        inner = result["result"]
        _assert_envelope(inner)
        assert inner["intent"] == "compare_drugs"

    def test_demo_metadata_source(self) -> None:
        """Demo results must be marked with source=demo_engine."""
        from backend.chatbot.demo import run_demo_case
        result = run_demo_case(case_id="safe_case")
        
        assert result["metadata"]["source"] == "demo_engine"
        assert result["metadata"]["scenario_id"] == "safe_case"
        assert "mode" in result["metadata"]
        assert "scope" in result["metadata"]

    def test_demo_deterministic_output(self) -> None:
        """Demo scenarios produce deterministic output (same input → same output)."""
        from backend.chatbot.demo import run_demo_case
        result1 = run_demo_case(case_id="safe_case", mode="doctor")
        result2 = run_demo_case(case_id="safe_case", mode="doctor")
        
        # Core outputs should be identical
        inner1 = result1["result"]
        inner2 = result2["result"]
        assert inner1["intent"] == inner2["intent"]
        assert inner1["template"] == inner2["template"]
        assert inner1["variables"] == inner2["variables"]

    def test_demo_mode_filter_applied(self) -> None:
        """Doctor and patient modes produce different outputs."""
        from backend.chatbot.demo import run_demo_case
        
        result_doctor = run_demo_case(case_id="safe_case", mode="doctor")
        result_patient = run_demo_case(case_id="safe_case", mode="patient")
        
        inner_doc = result_doctor["result"]
        inner_pat = result_patient["result"]
        
        # Mode metadata should differ
        assert result_doctor["metadata"]["mode"] == "doctor"
        assert result_patient["metadata"]["mode"] == "patient"
        
        # Patient mode should not expose modules
        assert "modules" in inner_doc["explanation"]
        assert "modules" not in inner_pat["explanation"]

    def test_demo_all_cases_runnable(self) -> None:
        """All demo cases should run without exceptions."""
        from backend.chatbot.demo import run_all_demo_cases
        results = run_all_demo_cases()
        
        assert isinstance(results, list)
        assert len(results) >= 3
        
        # Each result should be valid
        for result in results:
            assert "scenario" in result
            assert "metadata" in result
            # Should not have error field if successful
            if "error" not in result:
                assert "result" in result

    def test_invalid_case_id_raises_error(self) -> None:
        """Unknown case_id raises ValueError."""
        from backend.chatbot.demo import run_demo_case
        import pytest
        
        with pytest.raises(ValueError):
            run_demo_case(case_id="nonexistent_case")

    def test_demo_result_template_in_enum(self) -> None:
        """DEMO_RESULT is defined in TemplateCode enum."""
        assert hasattr(TemplateCode, "DEMO_RESULT")
        assert TemplateCode.DEMO_RESULT.value == "DEMO_RESULT"

    def test_demo_no_natural_language(self) -> None:
        """Demo scenarios output only structured data, no natural language."""
        from backend.chatbot.demo import run_demo_case
        result = run_demo_case(case_id="safe_case")
        
        # Template code must be uppercase, no spaces
        template = result["template"]
        assert template == template.upper()
        assert " " not in template
        
        # Inner response also must follow this rule
        inner_template = result["result"]["template"]
        assert inner_template == inner_template.upper()
        assert " " not in inner_template

    def test_decision_basis_codes_valid(self) -> None:
        """decision_basis should only contain allowed codes."""
        from backend.chatbot.comparator import TreatmentComparator
        comp = TreatmentComparator()
        
        result = comp.compare(
            drugs=["drugX", "drugY"],
            context={},
        )
        
        allowed_codes = {
            "LOWER_RISK",
            "LOWER_TOXICITY",
            "HIGHER_EFFECTIVENESS",
            "HIGHER_CONFIDENCE",
        }
        
        basis_codes = set(result["summary"]["decision_basis"])
        assert basis_codes.issubset(allowed_codes), (
            f"Invalid decision basis codes: {basis_codes - allowed_codes}"
        )

    def test_ranking_consistency(self) -> None:
        """Ranking should be deterministic (same input → same ranking)."""
        from backend.chatbot.comparator import TreatmentComparator
        comp = TreatmentComparator()
        
        drugs = ["penicillin", "cephalexin"]
        context = {}
        
        # Compare multiple times
        result1 = comp.compare(drugs=drugs, context=context)
        result2 = comp.compare(drugs=drugs, context=context)
        
        # Extract rankings
        ranking1 = sorted(result1["ranking"], key=lambda r: r["rank"])
        ranking2 = sorted(result2["ranking"], key=lambda r: r["rank"])
        
        # Should be identical
        assert ranking1 == ranking2
        assert result1["summary"]["best_option"] == result2["summary"]["best_option"]

    def test_comparator_with_genetic_context(self) -> None:
        """Comparator should handle genetic context."""
        from backend.chatbot.comparator import TreatmentComparator
        comp = TreatmentComparator()
        
        context = {
            "genetic_data": {
                "patient_metabolizer_status": "poor",
                "risk_alleles": ["CYP2D6*3", "CYP2D6*4"],
            }
        }
        
        result = comp.compare(
            drugs=["tramadol", "codeine"],
            context=context,
        )
        
        assert result["template"] in ("DRUG_COMPARISON", "INSUFFICIENT_DATA")
        if result["template"] == "DRUG_COMPARISON":
            assert len(result["ranking"]) == 2

    def test_comparator_metadata_present(self) -> None:
        """Metadata should track models invoked and any errors."""
        from backend.chatbot.comparator import TreatmentComparator
        comp = TreatmentComparator()
        
        result = comp.compare(
            drugs=["amoxicillin", "azithromycin"],
            context={},
        )
        
        assert "metadata" in result
        assert "source" in result["metadata"]
        assert result["metadata"]["source"] == "comparator"
        assert "models_invoked" in result["metadata"]
        assert isinstance(result["metadata"]["models_invoked"], list)


# ──────────────────────────────────────────────
#  7. Safety Guardrails
# ──────────────────────────────────────────────

class TestSafetyGuardrails:
    """Validates the SafetyGuardrails module."""

    def test_guardrails_import(self) -> None:
        """Verify guardrails module can be imported."""
        from backend.chatbot.guardrails import SafetyGuardrails
        gr = SafetyGuardrails()
        assert gr is not None

    def test_emergency_detection(self) -> None:
        """Emergency symptoms should trigger EMERGENCY guardrail."""
        from backend.chatbot.guardrails import SafetyGuardrails
        gr = SafetyGuardrails()
        
        emergency_queries = [
            "I have severe chest pain",
            "Can't breathe, difficulty breathing",
            "I think I'm having a stroke",
            "Severe uncontrolled bleeding",
        ]
        
        for query in emergency_queries:
            flag = gr.check(query)
            assert flag.triggered, f"Failed to detect emergency: {query}"
            assert flag.trigger_type == "EMERGENCY"
            assert flag.action_code == "SEEK_IMMEDIATE_HELP"
            assert flag.severity == "high"

    def test_self_medication_risk_detection(self) -> None:
        """Self-medication requests should trigger SELF_MEDICATION_RISK."""
        from backend.chatbot.guardrails import SafetyGuardrails
        gr = SafetyGuardrails()
        
        self_med_queries = [
            "What drug should I take without seeing a doctor?",
            "Which medicine can I use without consulting a physician?",
            "Can I take ciprofloxacin without doctor supervision?",
        ]
        
        for query in self_med_queries:
            flag = gr.check(query)
            assert flag.triggered, f"Failed to detect self-medication risk: {query}"
            assert flag.trigger_type == "SELF_MEDICATION_RISK"
            assert flag.action_code == "CONSULT_DOCTOR"

    def test_insufficient_context_detection(self) -> None:
        """Pharmacogenomic drugs without genetic data should trigger."""
        from backend.chatbot.guardrails import SafetyGuardrails
        gr = SafetyGuardrails()
        
        # Querying about tramadol without genetic context
        flag = gr.check(
            user_input="Is tramadol safe for me?",
            context={},  # No genetic_data
        )
        assert flag.triggered
        assert flag.trigger_type == "INSUFFICIENT_CONTEXT_CRITICAL"
        assert flag.action_code == "PROVIDE_MORE_INFO"

    def test_high_uncertainty_detection(self) -> None:
        """Extremely vague queries should trigger HIGH_UNCERTAINTY."""
        from backend.chatbot.guardrails import SafetyGuardrails
        gr = SafetyGuardrails()
        
        vague_queries = [
            "I feel bad",
            "Something is wrong",
            "Help",
        ]
        
        for query in vague_queries:
            flag = gr.check(query)
            assert flag.triggered, f"Failed to detect high uncertainty: {query}"
            assert flag.trigger_type == "HIGH_UNCERTAINTY"
            assert flag.action_code == "PROVIDE_MORE_INFO"

    def test_normal_query_passes_through(self) -> None:
        """Normal medical queries should not trigger guardrails."""
        from backend.chatbot.guardrails import SafetyGuardrails
        gr = SafetyGuardrails()
        
        normal_queries = [
            "What is the toxicity of amoxicillin?",
            "Is ciprofloxacin contraindicated with my genetic profile?",
            "Compare these two antibiotics",
        ]
        
        for query in normal_queries:
            flag = gr.check(query, context={"genetic_data": {}})
            assert not flag.triggered, f"Incorrectly flagged normal query: {query}"

    def test_safety_response_structure(self) -> None:
        """Safety response should have correct structure."""
        from backend.chatbot.guardrails import SafetyGuardrails, SafetyFlag
        gr = SafetyGuardrails()
        
        flag = SafetyFlag(
            triggered=True,
            trigger_type="EMERGENCY",
            action_code="SEEK_IMMEDIATE_HELP",
            severity="high",
            confidence=0.95,
        )
        
        response = gr.get_safety_response(flag)
        
        # Required keys
        assert "intent" in response
        assert "template" in response
        assert "variables" in response
        assert "safety" in response
        assert "metadata" in response
        
        # Correct intent
        assert response["intent"] == "safety_guardrail"
        assert response["template"] == "SAFETY_WARNING"
        
        # Safety payload
        assert response["safety"]["severity"] == "high"
        assert response["safety"]["action_code"] == "SEEK_IMMEDIATE_HELP"
        
        # Metadata
        assert response["metadata"]["source"] == "guardrails"

    def test_action_codes_valid(self) -> None:
        """Action codes should only come from allowed set."""
        from backend.chatbot.guardrails import SafetyGuardrails
        gr = SafetyGuardrails()
        
        allowed_codes = {
            "SEEK_IMMEDIATE_HELP",
            "CONSULT_DOCTOR",
            "PROVIDE_MORE_INFO",
            "LIMITED_ASSISTANCE",
        }
        
        test_queries = [
            ("I have chest pain", "SEEK_IMMEDIATE_HELP"),
            ("What drug should I take?", "CONSULT_DOCTOR"),
            ("I feel bad", "PROVIDE_MORE_INFO"),
        ]
        
        for query, expected_code in test_queries:
            flag = gr.check(query)
            if flag.triggered:
                assert flag.action_code in allowed_codes
                # Verify expected behavior
                if expected_code in allowed_codes:
                    assert flag.action_code == expected_code

    def test_guardrails_integration_with_controller(self) -> None:
        """Guardrails should run first in the controller pipeline."""
        # Emergency query should return safety response, not normal pipeline
        resp = process_query(
            user_input="I have severe chest pain and can't breathe",
            mode="doctor",
            context={},
        )
        
        # Should be safety response
        assert resp["intent"] == "safety_guardrail"
        assert resp["template"] == TemplateCode.SAFETY_WARNING.value
        assert "safety" in resp
        assert resp["safety"]["action_code"] == "SEEK_IMMEDIATE_HELP"

    def test_guardrails_blocks_before_pipeline(self) -> None:
        """Safety responses should not enter normal processing pipeline."""
        # Self-medication risk should trigger, not go to normal intent detection
        resp = process_query(
            user_input="What drug should I take without seeing a doctor?",
            mode="doctor",
            context={},
        )
        
        assert resp["intent"] == "safety_guardrail"
        # Should NOT have gone through normal pipeline
        assert "models_invoked" not in resp.get("metadata", {}) or \
               resp["metadata"].get("models_invoked") is None

    def test_guardrails_confidence_scores(self) -> None:
        """Safety flags should have confidence scores."""
        from backend.chatbot.guardrails import SafetyGuardrails
        gr = SafetyGuardrails()
        
        flag = gr.check("I have severe chest pain")
        assert flag.triggered
        assert 0.0 <= flag.confidence <= 1.0
        assert flag.confidence > 0.8  # Emergency should have high confidence

    def test_guardrails_deterministic(self) -> None:
        """Same dangerous input should trigger same guardrail."""
        from backend.chatbot.guardrails import SafetyGuardrails
        gr = SafetyGuardrails()
        
        query = "I have chest pain"
        
        flag1 = gr.check(query)
        flag2 = gr.check(query)
        
        assert flag1.triggered == flag2.triggered
        assert flag1.trigger_type == flag2.trigger_type
        assert flag1.action_code == flag2.action_code
        assert flag1.severity == flag2.severity

    def test_no_natural_language_in_safety_response(self) -> None:
        """Safety response should not contain natural language."""
        resp = process_query(
            user_input="I have chest pain",
            mode="doctor",
            context={},
        )
        
        # No sentences in variables
        for key, value in resp.get("variables", {}).items():
            if isinstance(value, str):
                # Should be a code like "EMERGENCY", not "You are experiencing an emergency"
                assert value == value.upper() or len(value.split()) == 1, (
                    f"Natural language detected in variables: {value}"
                )
        
        # Action code should be uppercase
        action_code = resp["safety"]["action_code"]
        assert action_code == action_code.replace(" ", "_")  # Underscores, not spaces
        assert action_code.isupper()  # Uppercase code, not sentence

    def test_guardrails_mode_independent(self) -> None:
        """Guardrails should trigger in both doctor and patient modes."""
        query = "I have severe bleeding"
        
        resp_doc = process_query(query, mode="doctor", context={})
        resp_pat = process_query(query, mode="patient", context={})
        
        # Both should trigger safety
        assert resp_doc["intent"] == "safety_guardrail"
        assert resp_pat["intent"] == "safety_guardrail"
        
        assert resp_doc["safety"]["action_code"] == resp_pat["safety"]["action_code"]

# ──────────────────────────────────────────────
#  8. Guidance Engine Tests
# ──────────────────────────────────────────────

class TestInputGuidanceEngine:
    """Validates the Input Guidance Engine logic."""

    def test_no_input_from_compare_intent(self) -> None:
        """compare_drugs with drugs but no genetic/infection data → guidance triggered"""
        resp = process_query(
            user_input="Compare these medications",
            mode="doctor",
            context={"drugs": ["amoxicillin", "ciprofloxacin"]}  # Has drugs, but missing genetic/infection
        )
        assert resp["intent"] == "input_guidance"
        assert resp["template"] == TemplateCode.REQUEST_MISSING_INFO.value
        assert "genetic_data" in resp["variables"]["missing_fields"]
        assert "infection_data" in resp["variables"]["missing_fields"]
        assert len(resp["guidance"]) == 2

    def test_partial_input(self) -> None:
        """Partial input → detect remaining fields"""
        resp = process_query(
            user_input="Compare these medications",
            mode="doctor",
            context={
                "drugs": ["amoxicillin", "ciprofloxacin"],
                "genetic_data": {"markers": ["CYP2D6"]}
            }
        )
        assert resp["intent"] == "input_guidance"
        assert resp["template"] == TemplateCode.REQUEST_MISSING_INFO.value
        assert "infection_data" in resp["variables"]["missing_fields"]
        assert "genetic_data" not in resp["variables"]["missing_fields"]
        assert len(resp["guidance"]) == 1
        assert resp["guidance"][0]["field"] == "infection_data"
        assert resp["guidance"][0]["question_code"] == "ASK_INFECTION_TYPE"

    def test_full_input(self) -> None:
        """Full input → guidance NOT triggered"""
        resp = process_query(
            user_input="Compare these medications",
            mode="doctor",
            context={
                "genetic_data": {"markers": ["CYP2D6"]},
                "infection_data": {"pathogen": "MRSA"},
                "drug": "warfarin"
            }
        )
        assert resp["intent"] != "input_guidance"
        assert resp["template"] != TemplateCode.REQUEST_MISSING_INFO.value


# ──────────────────────────────────────────────
#  9. Report Generation Tests
# ──────────────────────────────────────────────

class TestReportEngine:
    """Validates the Report Generation Engine."""

    def test_report_engine_import(self) -> None:
        """Verify report engine module can be imported."""
        from backend.chatbot.report import ReportEngine
        engine = ReportEngine()
        assert engine is not None

    def test_generate_valid_report(self) -> None:
        """Generate a valid report from a complete last_response."""
        from backend.chatbot.report import ReportEngine
        engine = ReportEngine()
        
        last_response = {
            "intent": "drug_analysis",
            "template": TemplateCode.DRUG_NOT_RECOMMENDED.value,
            "variables": {
                "drug_name": "warfarin",
                "risk_level": "high",
                "confidence_score": 0.92,
                "recommended_option": "Use caution with genetic testing",
            },
            "explanation": {
                "reason_codes": ["high_toxicity", "adverse_genetic"],
                "reason_details": [],
                "modules": {
                    "toxicity_analysis": {"score": 0.9},
                    "genetic_analysis": {"score": 0.85}
                }
            },
            "metadata": {"linked_response_id": "test-123"}
        }
        
        report = engine.generate(context={"last_response": last_response})
        
        # Verify intent and template
        assert report["intent"] == "generate_report"
        assert report["template"] == TemplateCode.REPORT_READY.value
        
        # Verify report envelope
        assert "report" in report
        assert "metadata" in report
        assert report["metadata"]["source"] == "report_engine"

    def test_report_structure(self) -> None:
        """Verify report has correct nested structure."""
        from backend.chatbot.report import ReportEngine
        engine = ReportEngine()
        
        last_response = {
            "variables": {
                "recommended_option": "amoxicillin",
                "confidence_score": 0.87,
                "risk_level": "low",
            },
            "explanation": {
                "reason_codes": ["low_toxicity"],
                "reason_details": [],
                "modules": {"toxicity_analysis": {"score": 0.2}}
            }
        }
        
        report = engine.generate(context={"last_response": last_response})
        
        # Verify structure
        assert "report" in report
        assert "summary" in report["report"]
        assert "risk_analysis" in report["report"]
        assert "decision_factors" in report["report"]
        
        # Verify summary
        assert report["report"]["summary"]["recommended_option"] == "amoxicillin"
        assert report["report"]["summary"]["confidence"] == 0.87
        
        # Verify risk_analysis
        assert report["report"]["risk_analysis"]["risk_level"] == "low"
        assert report["report"]["risk_analysis"]["reason_codes"] == ["low_toxicity"]
        
        # Verify decision_factors
        assert "modules" in report["report"]["decision_factors"]
        assert "toxicity_analysis" in report["report"]["decision_factors"]["modules"]

    def test_report_missing_context(self) -> None:
        """Report with missing last_response should return INSUFFICIENT_CONTEXT."""
        from backend.chatbot.report import ReportEngine
        engine = ReportEngine()
        
        report = engine.generate(context={})
        
        assert report["intent"] == "generate_report"
        assert report["template"] == TemplateCode.INSUFFICIENT_CONTEXT.value
        assert report["variables"] == {}

    def test_report_risks_extraction(self) -> None:
        """Verify risk level extraction from various sources."""
        from backend.chatbot.report import ReportEngine
        engine = ReportEngine()
        
        # Risk from variables
        report1 = engine.generate(context={
            "last_response": {
                "variables": {"risk_level": "medium"},
                "explanation": {
                    "reason_codes": [],
                    "reason_details": [],
                    "modules": {}
                }
            }
        })
        assert report1["report"]["risk_analysis"]["risk_level"] == "medium"
        
        # Risk from reason_codes
        report2 = engine.generate(context={
            "last_response": {
                "variables": {},
                "explanation": {
                    "reason_codes": ["high_toxicity"],
                    "reason_details": [],
                    "modules": {}
                }
            }
        })
        assert report2["report"]["risk_analysis"]["risk_level"] == "high"
        
        # Risk from toxicity_score
        report3 = engine.generate(context={
            "last_response": {
                "variables": {},
                "explanation": {
                    "reason_codes": [],
                    "reason_details": [],
                    "modules": {
                        "toxicity_analysis": {"score": 0.5}
                    }
                }
            }
        })
        assert report3["report"]["risk_analysis"]["risk_level"] == "medium"

    def test_report_no_natural_language(self) -> None:
        """Report should not contain human-readable sentences."""
        from backend.chatbot.report import ReportEngine
        engine = ReportEngine()
        
        # Create a report with various data
        last_response = {
            "variables": {
                "drug_name": "aspirin",
                "risk_level": "low",
                "recommended_option": "safe_option",
                "confidence_score": 0.95,
            },
            "explanation": {
                "reason_codes": ["LOW_TOXICITY", "NO_INTERACTIONS"],
                "reason_details": [],
                "modules": {
                    "toxicity_analysis": {"score": 0.2},
                    "interaction_analysis": {"found": None}
                }
            }
        }
        
        report = engine.generate(context={"last_response": last_response})
        
        # Template should be uppercase code
        assert report["template"] == report["template"].upper()
        assert " " not in report["template"]
        
        # Intent should be specific code
        assert report["intent"] == "generate_report"
        
        # Risk code should be uppercase
        risk_level = report["report"]["risk_analysis"]["risk_level"]
        if risk_level:  # Can be None
            assert risk_level in ("low", "medium", "high")
        
        # Reason codes should be uppercase
        for code in report["report"]["risk_analysis"]["reason_codes"]:
            assert isinstance(code, str)
            assert "_" not in code or code == code.upper()  # Either no underscore or all upper

    def test_report_all_fields_present(self) -> None:
        """Verify all required fields are present in report."""
        from backend.chatbot.report import ReportEngine
        engine = ReportEngine()
        
        last_response = {
            "variables": {
                "recommended_option": "drug_A",
                "confidence_score": 0.80,
            },
            "explanation": {
                "reason_codes": ["reason1"],
                "reason_details": [],
                "modules": {"analysis": {"data": "value"}}
            }
        }
        
        report = engine.generate(context={"last_response": last_response})
        
        # Required top-level keys
        assert "intent" in report
        assert "template" in report
        assert "report" in report
        assert "metadata" in report
        
        # Required report keys
        assert "summary" in report["report"]
        assert "risk_analysis" in report["report"]
        assert "decision_factors" in report["report"]
        
        # Required summary keys
        assert "recommended_option" in report["report"]["summary"]
        assert "confidence" in report["report"]["summary"]
        
        # Required risk_analysis keys
        assert "risk_level" in report["report"]["risk_analysis"]
        assert "reason_codes" in report["report"]["risk_analysis"]
        
        # Required decision_factors keys
        assert "modules" in report["report"]["decision_factors"]

    def test_report_deterministic(self) -> None:
        """Same input should produce identical output."""
        from backend.chatbot.report import ReportEngine
        engine = ReportEngine()
        
        context = {
            "last_response": {
                "variables": {
                    "recommended_option": "test_drug",
                    "confidence_score": 0.75,
                    "risk_level": "medium",
                },
                "explanation": {
                    "reason_codes": ["TEST_REASON"],
                    "reason_details": [],
                    "modules": {"test": {"val": 42}}
                }
            }
        }
        
        report1 = engine.generate(context=context)
        report2 = engine.generate(context=context)
        
        # Should be identical
        assert report1 == report2
        assert report1["report"]["summary"] == report2["report"]["summary"]
        assert report1["report"]["risk_analysis"] == report2["report"]["risk_analysis"]


# ──────────────────────────────────────────────
#  10. UI Adapter Layer Tests
# ──────────────────────────────────────────────

class TestUIAdapter:
    """Validates the UI Adapter Layer."""

    def test_ui_adapter_import(self) -> None:
        """Verify UI adapter module can be imported."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        assert adapter is not None

    def test_comparison_response_to_ui(self) -> None:
        """Transform comparison response into comparison_view."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "compare_drugs",
            "template": TemplateCode.COMPARISON_RESULT.value,
            "variables": {
                "drugs_compared": ["amoxicillin", "ciprofloxacin"],
                "recommended_drug": "amoxicillin",
            },
            "comparison": [
                {"drug": "amoxicillin", "risk_level": "low"},
                {"drug": "ciprofloxacin", "risk_level": "medium"},
            ],
            "ranking": [
                {"drug": "amoxicillin", "rank": 1},
                {"drug": "ciprofloxacin", "rank": 2},
            ],
            "summary": {
                "best_option": "amoxicillin",
                "decision_basis": ["LOWER_TOXICITY"],
            },
            "explanation": {
                "reason_codes": ["lower_risk"],
                "reason_details": [],
                "modules": {"toxicity_analysis": {"score": 0.2}},
            },
            "metadata": {"processing_time_ms": 45.2},
        }
        
        ui_response = adapter.adapt(response)
        
        assert ui_response["ui_type"] == "comparison_view"
        assert len(ui_response["components"]) > 0
        assert ui_response["metadata"]["template"] == TemplateCode.COMPARISON_RESULT.value
        
        # Verify comparison table component exists
        comparison_components = [c for c in ui_response["components"] if c["type"] == "comparison_table"]
        assert len(comparison_components) == 1
        assert comparison_components[0]["data"]["comparison"] == response["comparison"]

    def test_report_response_to_ui(self) -> None:
        """Transform report response into report_view."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "generate_report",
            "template": TemplateCode.REPORT_READY.value,
            "report": {
                "summary": {
                    "recommended_option": "warfarin",
                    "confidence": 0.92,
                },
                "risk_analysis": {
                    "risk_level": "high",
                    "reason_codes": ["high_toxicity"],
                },
                "decision_factors": {
                    "modules": {"toxicity_analysis": {"score": 0.9}},
                },
            },
            "metadata": {"source": "report_engine"},
        }
        
        ui_response = adapter.adapt(response)
        
        assert ui_response["ui_type"] == "report_view"
        assert len(ui_response["components"]) > 0
        
        # Verify report components exist
        report_summary_components = [c for c in ui_response["components"] if c["type"] == "report_summary"]
        assert len(report_summary_components) == 1
        
        risk_analysis_components = [c for c in ui_response["components"] if c["type"] == "risk_analysis"]
        assert len(risk_analysis_components) == 1

    def test_guidance_response_to_ui(self) -> None:
        """Transform guidance response into input_form."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "input_guidance",
            "template": TemplateCode.REQUEST_MISSING_INFO.value,
            "variables": {
                "missing_fields": ["genetic_data", "infection_data"],
            },
            "guidance": [
                {
                    "field": "genetic_data",
                    "question_code": "ASK_GENETIC_DATA",
                },
                {
                    "field": "infection_data",
                    "question_code": "ASK_INFECTION_TYPE",
                },
            ],
            "metadata": {},
        }
        
        ui_response = adapter.adapt(response)
        
        assert ui_response["ui_type"] == "input_form"
        assert len(ui_response["components"]) > 0
        
        # Verify guidance form component exists
        form_components = [c for c in ui_response["components"] if c["type"] == "guidance_form"]
        assert len(form_components) == 1
        assert form_components[0]["data"]["guidance"] == response["guidance"]

    def test_alert_card_mapping(self) -> None:
        """Test alert card template mapping."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "drug_analysis",
            "template": TemplateCode.DRUG_NOT_RECOMMENDED.value,
            "variables": {
                "drug_name": "warfarin",
                "risk_level": "high",
            },
            "explanation": {
                "reason_codes": ["high_toxicity", "adverse_genetic"],
                "reason_details": [],
                "modules": {},
            },
            "metadata": {},
        }
        
        ui_response = adapter.adapt(response)
        
        assert ui_response["ui_type"] == "alert_card"
        
        # Verify alert card component
        alert_components = [c for c in ui_response["components"] if c["type"] == "alert_card"]
        assert len(alert_components) == 1
        assert alert_components[0]["data"]["risk_level"] == "high"
        assert alert_components[0]["data"]["reason_codes"] == ["high_toxicity", "adverse_genetic"]

    def test_explanation_view_mapping(self) -> None:
        """Test explanation view template mapping."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "explain_result",
            "template": TemplateCode.EXPLANATION_SUMMARY.value,
            "variables": {"scope": "toxicity"},
            "explanation": {
                "reason_codes": ["high_toxicity", "contraindicated"],
                "reason_details": [{"code": "HIGH_TOXICITY", "module": "toxicity", "severity": "high"}],
                "modules": {"toxicity_analysis": {"score": 0.9}},
            },
            "metadata": {},
        }
        
        ui_response = adapter.adapt(response)
        
        assert ui_response["ui_type"] == "explanation_view"
        assert len(ui_response["components"]) > 0
        
        # Verify explanation components exist
        reason_components = [c for c in ui_response["components"] if c["type"] == "reason_codes_list"]
        assert len(reason_components) == 1
        assert reason_components[0]["data"]["reason_codes"] == ["high_toxicity", "contraindicated"]

    def test_warning_alert_mapping(self) -> None:
        """Test warning alert for safety guardrails."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "safety_guardrail",
            "template": TemplateCode.SAFETY_WARNING.value,
            "variables": {
                "type": "HIGH_UNCERTAINTY",
            },
            "safety": {
                "severity": "low",
                "action_code": "PROVIDE_MORE_INFO",
            },
            "metadata": {"source": "guardrails"},
        }
        
        ui_response = adapter.adapt(response)
        
        assert ui_response["ui_type"] == "warning_alert"
        
        # Verify warning component
        warning_components = [c for c in ui_response["components"] if c["type"] == "warning_alert"]
        assert len(warning_components) == 1
        assert warning_components[0]["data"]["safety"]["action_code"] == "PROVIDE_MORE_INFO"

    def test_safe_default_for_unknown_template(self) -> None:
        """Unknown template should return generic_view."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "unknown_intent",
            "template": "UNKNOWN_TEMPLATE",
            "variables": {},
            "metadata": {},
        }
        
        ui_response = adapter.adapt(response)
        
        assert ui_response["ui_type"] == "generic_view"
        assert ui_response["components"] == []

    def test_metadata_extraction(self) -> None:
        """Verify metadata is correctly extracted for multilingual support."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "drug_analysis",
            "template": TemplateCode.DRUG_NOT_RECOMMENDED.value,
            "variables": {"risk_level": "high"},
            "explanation": {"reason_codes": [], "reason_details": [], "modules": {}},
            "metadata": {
                "processing_time_ms": 42.5,
                "intent_confidence": 0.95,
                "mode": "doctor",
            },
        }
        
        ui_response = adapter.adapt(response)
        
        # Verify metadata preservation (for multilingual support)
        assert ui_response["metadata"]["template"] == TemplateCode.DRUG_NOT_RECOMMENDED.value
        assert ui_response["metadata"]["intent"] == "drug_analysis"
        assert ui_response["metadata"]["processing_time_ms"] == 42.5
        assert ui_response["metadata"]["intent_confidence"] == 0.95
        assert ui_response["metadata"]["mode"] == "doctor"

    def test_no_text_generation(self) -> None:
        """Verify no text is generated - only codes and structured data."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "drug_analysis",
            "template": TemplateCode.DRUG_NOT_RECOMMENDED.value,
            "variables": {
                "drug_name": "warfarin",
                "risk_level": "high",
            },
            "explanation": {
                "reason_codes": ["HIGH_TOXICITY"],
                "reason_details": [],
                "modules": {"toxicity_analysis": {"score": 0.9}},
            },
            "metadata": {},
        }
        
        ui_response = adapter.adapt(response)
        
        # Verify no generated text
        def check_no_sentences(obj: Any) -> None:
            """Recursively check that no natural language sentences exist."""
            if isinstance(obj, dict):
                for value in obj.values():
                    check_no_sentences(value)
            elif isinstance(obj, list):
                for item in obj:
                    check_no_sentences(item)
            elif isinstance(obj, str):
                # Strings should be codes (uppercase with underscores) or empty
                # Not complete sentences with spaces
                if len(obj) > 20 and " " in obj:
                    # Could be natural language - flag it
                    assert False, f"Potential natural language found: {obj}"
        
        check_no_sentences(ui_response)

    def test_component_structure_consistency(self) -> None:
        """Verify all components have consistent structure."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "compare_drugs",
            "template": TemplateCode.COMPARISON_RESULT.value,
            "variables": {},
            "comparison": [{"drug": "drug1"}],
            "ranking": [{"drug": "drug1", "rank": 1}],
            "summary": {"best_option": "drug1"},
            "explanation": {
                "reason_codes": [],
                "reason_details": [],
                "modules": {},
            },
            "metadata": {},
        }
        
        ui_response = adapter.adapt(response)
        
        # All components must have 'type' and 'data'
        for component in ui_response["components"]:
            assert "type" in component, "Component missing type"
            assert "data" in component, "Component missing data"
            assert isinstance(component["type"], str), "Type must be string"
            assert isinstance(component["data"], dict), "Data must be dict"

    def test_success_card_mapping(self) -> None:
        """Test success card for safe drugs."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "drug_analysis",
            "template": TemplateCode.SAFE_TO_USE.value,
            "variables": {
                "drug_name": "aspirin",
                "risk_level": "low",
            },
            "explanation": {
                "reason_codes": ["LOW_TOXICITY"],
                "reason_details": [],
                "modules": {"toxicity_analysis": {"score": 0.2}},
            },
            "metadata": {},
        }
        
        ui_response = adapter.adapt(response)
        
        assert ui_response["ui_type"] == "success_card"
        
        # Verify success card component
        success_components = [c for c in ui_response["components"] if c["type"] == "success_card"]
        assert len(success_components) == 1
        assert success_components[0]["data"]["risk_level"] == "low"

    def test_deterministic_transformation(self) -> None:
        """Same input should produce identical UI output."""
        from backend.chatbot.ui_adapter import UIAdapter
        adapter = UIAdapter()
        
        response = {
            "intent": "drug_analysis",
            "template": TemplateCode.DRUG_NOT_RECOMMENDED.value,
            "variables": {"risk_level": "high"},
            "explanation": {
                "reason_codes": ["reason1"],
                "reason_details": [],
                "modules": {},
            },
            "metadata": {"processing_time_ms": 50},
        }
        
        ui_response1 = adapter.adapt(response)
        ui_response2 = adapter.adapt(response)
        
        # Should be identical
        assert ui_response1 == ui_response2

