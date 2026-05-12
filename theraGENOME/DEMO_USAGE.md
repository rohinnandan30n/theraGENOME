"""
TheraGenome AI — Demo Mode Usage Examples
==========================================
Quick reference for using the demo engine in presentations and testing.
"""

# ──────────────────────────────────────────────
#  Example 1: List Available Scenarios
# ──────────────────────────────────────────────

from backend.chatbot.demo import get_demo_cases

cases = get_demo_cases()

print("Available Demo Scenarios:")
for case in cases:
    print(f"  • {case['id']}: {case['name']}")
    print(f"    → {case['description']}")

# Output:
# Available Demo Scenarios:
#   • safe_case: Safe Treatment Case
#     → Patient with no drug interactions; safe to use
#   • high_risk_case: High-Risk Case
#     → Patient with genetic contraindications; requires caution
#   • comparison_case: Multi-Drug Comparison
#     → Compare efficacy and safety of two antibiotics


# ──────────────────────────────────────────────
#  Example 2: Run a Single Demo Scenario
# ──────────────────────────────────────────────

from backend.chatbot.demo import run_demo_case
import json

# Run the safe case scenario
result = run_demo_case(case_id="safe_case", mode="doctor")

# The result has this structure:
# {
#     "intent": "demo_run",
#     "template": "DEMO_RESULT",
#     "scenario": {
#         "id": "safe_case",
#         "name": "Safe Treatment Case",
#         "description": "..."
#     },
#     "result": {
#         # Full process_query() response
#         "intent": "drug_analysis",
#         "template": "SAFE_TO_USE" | "DRUG_USE_WITH_CAUTION" | "DRUG_NOT_RECOMMENDED",
#         "variables": {...},
#         "explanation": {...},
#         "metadata": {...}
#     },
#     "metadata": {
#         "source": "demo_engine",
#         "scenario_id": "safe_case",
#         "mode": "doctor",
#         "scope": "full"
#     }
# }

print(f"Scenario: {result['scenario']['name']}")
print(f"Intent: {result['result']['intent']}")
print(f"Risk Level: {result['result']['variables'].get('risk_level')}")
print(f"Drug: {result['result']['variables'].get('drug_name')}")


# ──────────────────────────────────────────────
#  Example 3: Run All Scenarios (Batch)
# ──────────────────────────────────────────────

from backend.chatbot.demo import run_all_demo_cases

results = run_all_demo_cases(mode="doctor")

print(f"Executed {len(results)} scenarios:")
for r in results:
    scenario = r["scenario"]
    inner = r.get("result", {})
    print(f"✓ {scenario['id']}: {inner.get('template', 'ERROR')}")


# ──────────────────────────────────────────────
#  Example 4: Patient vs Doctor Mode
# ──────────────────────────────────────────────

from backend.chatbot.demo import run_demo_case

# Doctor mode: includes full model outputs
result_doctor = run_demo_case("high_risk_case", mode="doctor")
inner_doctor = result_doctor["result"]

# Patient mode: simplified, no raw model data
result_patient = run_demo_case("high_risk_case", mode="patient")
inner_patient = result_patient["result"]

print("Doctor Mode:")
print(f"  Modules exposed: {'modules' in inner_doctor['explanation']}")

print("Patient Mode:")
print(f"  Modules exposed: {'modules' in inner_patient['explanation']}")


# ──────────────────────────────────────────────
#  Example 5: Comparison Scenario
# ──────────────────────────────────────────────

from backend.chatbot.demo import run_demo_case

result = run_demo_case("comparison_case", mode="doctor")
inner = result["result"]

print(f"Comparison: {inner['variables'].get('drugs_compared')}")
print(f"Recommended: {inner['variables'].get('recommended_drug')}")
print(f"Template: {inner['template']}")  # COMPARISON_RESULT


# ──────────────────────────────────────────────
#  Key Properties of Demo Results
# ──────────────────────────────────────────────

# 1. DETERMINISTIC: Same input → same output (no randomness)
result1 = run_demo_case("safe_case")
result2 = run_demo_case("safe_case")
assert result1["result"]["template"] == result2["result"]["template"]

# 2. NO NATURAL LANGUAGE: Only machine-readable template codes
assert result["template"] == result["template"].upper()  # Uppercase code
assert " " not in result["template"]                     # No spaces

# 3. REAL PIPELINE: Data flows through process_query() unmodified
# The demo engine doesn't fake outputs — it uses the real decision engine

# 4. SOURCE TRACKING: Responses are marked with source="demo_engine"
assert result["metadata"]["source"] == "demo_engine"

# 5. MODE AWARE: Respects doctor/patient mode settings
# Doctor mode includes raw model data
# Patient mode strips sensitive details
