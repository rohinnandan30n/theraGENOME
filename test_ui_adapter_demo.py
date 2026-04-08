"""Quick validation of UI adapter functionality."""

from backend.chatbot.ui_adapter import UIAdapter
from backend.chatbot.templates import TemplateCode

adapter = UIAdapter()

# Example 1: Comparison response
print("="*60)
print("Example 1: Comparison Response → comparison_view")
print("="*60)

comparison_resp = {
    "intent": "compare_drugs",
    "template": TemplateCode.COMPARISON_RESULT.value,
    "variables": {"drugs_compared": ["amoxicillin", "ciprofloxacin"]},
    "comparison": [
        {"drug": "amoxicillin", "risk_level": "low"},
    ],
    "ranking": [{"drug": "amoxicillin", "rank": 1}],
    "summary": {"best_option": "amoxicillin"},
    "explanation": {
        "reason_codes": ["LOWER_TOXICITY"],
        "reason_details": [],
        "modules": {"toxicity_analysis": {"score": 0.2}},
    },
    "metadata": {"processing_time_ms": 45},
}

ui_resp = adapter.adapt(comparison_resp)
print(f"UI Type: {ui_resp['ui_type']}")
print(f"Components: {len(ui_resp['components'])} total")
for comp in ui_resp["components"]:
    print(f"  - {comp['type']}")

# Example 2: Report response
print("\n" + "="*60)
print("Example 2: Report Response → report_view")
print("="*60)

report_resp = {
    "intent": "generate_report",
    "template": TemplateCode.REPORT_READY.value,
    "report": {
        "summary": {"recommended_option": "warfarin", "confidence": 0.92},
        "risk_analysis": {"risk_level": "high", "reason_codes": ["HIGH_TOXICITY"]},
        "decision_factors": {"modules": {"toxicity_analysis": {"score": 0.9}}},
    },
    "metadata": {"source": "report_engine"},
}

ui_resp2 = adapter.adapt(report_resp)
print(f"UI Type: {ui_resp2['ui_type']}")
print(f"Components: {len(ui_resp2['components'])} total")
for comp in ui_resp2["components"]:
    print(f"  - {comp['type']}")

# Example 3: Guidance response
print("\n" + "="*60)
print("Example 3: Guidance Response → input_form")
print("="*60)

guidance_resp = {
    "intent": "input_guidance",
    "template": TemplateCode.REQUEST_MISSING_INFO.value,
    "variables": {"missing_fields": ["genetic_data"]},
    "guidance": [
        {
            "field": "genetic_data",
            "question_code": "ASK_GENETIC_DATA",
        }
    ],
    "metadata": {},
}

ui_resp3 = adapter.adapt(guidance_resp)
print(f"UI Type: {ui_resp3['ui_type']}")
print(f"Components: {len(ui_resp3['components'])} total")
for comp in ui_resp3["components"]:
    print(f"  - {comp['type']}")

# Example 4: Alert card (safety warning)
print("\n" + "="*60)
print("Example 4: Safety Response → warning_alert")
print("="*60)

safety_resp = {
    "intent": "safety_guardrail",
    "template": TemplateCode.SAFETY_WARNING.value,
    "variables": {"type": "HIGH_UNCERTAINTY"},
    "safety": {
        "severity": "low",
        "action_code": "PROVIDE_MORE_INFO",
    },
    "metadata": {"source": "guardrails"},
}

ui_resp4 = adapter.adapt(safety_resp)
print(f"UI Type: {ui_resp4['ui_type']}")
print(f"Components: {len(ui_resp4['components'])} total")
for comp in ui_resp4["components"]:
    print(f"  - {comp['type']}")

# Metadata preservation
print("\n" + "="*60)
print("Metadata Preserved for Multilingual Support")
print("="*60)
print(f"Template Code: {ui_resp['metadata']['template']}")
print(f"Intent: {ui_resp['metadata']['intent']}")
print(f"Processing Time: {ui_resp['metadata']['processing_time_ms']}ms")
print(f"Mode: {ui_resp['metadata']['mode']}")

print("\n✅ All UI adapter demonstrations completed successfully!")
