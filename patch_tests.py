import re

def patch_tests():
    with open("backend/tests/test_chatbot.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Patch _assert_envelope
    new_assert = '''def _assert_envelope(resp: dict) -> None:
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
    
    if resp["intent"] not in ("input_guidance", "safety_guardrail") and resp["template"] != TemplateCode.INSUFFICIENT_CONTEXT.value:
        assert "linked_response_id" in resp["metadata"]

    assert resp["template"] in [t.value for t in TemplateCode], f"Unknown template: {resp['template']}"'''

    old_assert = '''def _assert_envelope(resp: dict) -> None:
    """Every response must have the canonical envelope keys."""
    for key in ("intent", "template", "variables", "explanation", "metadata"):
        assert key in resp, f"Missing key: {key}"
    
    assert "reason_codes" in resp["explanation"]
    assert "reason_details" in resp["explanation"]
    
    if resp["template"] != TemplateCode.INSUFFICIENT_CONTEXT.value:
        assert "linked_response_id" in resp["metadata"]

    # Template must be a valid code
    assert resp["template"] in [t.value for t in TemplateCode], (
        f"Unknown template: {resp['template']}"
    )'''
    content = content.replace(old_assert, new_assert)

    # 2. Add required context to tests in TestDrugAnalysis, TestCompareDrugs, TestEdgeCases
    # We will just inject these required fields into the Context dictionaries directly.
    # e.g., context={"drug": "ciprofloxacin"} -> context={"drug": "ciprofloxacin", "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}}
    
    replacements = [
        ('context={"drug": "ciprofloxacin"},', 'context={"drug": "ciprofloxacin", "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},'),
        ('context={"drug": "metformin"},', 'context={"drug": "metformin", "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},'),
        ('context={"drug": "warfarin"},', 'context={"drug": "warfarin", "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},'),
        ('context={"drug": "aspirin"},', 'context={"drug": "aspirin", "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},'),
        ('context={"drugs": ["amoxicillin", "doxycycline"]},', 'context={"drugs": ["amoxicillin", "doxycycline"], "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},'),
        ('context={"drugs": ["drugA", "drugB"]},', 'context={"drugs": ["drugA", "drugB"], "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}},'),
        ('context={"drugs": ["drugA", "drugB"]}', 'context={"drugs": ["drugA", "drugB"], "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}}'),
        ('context={"genetic_data": {"markers": ["CYP2D6"]}},', 'context={"genetic_data": {"markers": ["CYP2D6"]}, "infection_data": {"a":"b"}},'),
        ('context={"infection_data": {"pathogen": "MRSA"}},', 'context={"infection_data": {"pathogen": "MRSA"}, "genetic_data": {"x":"y"}},'),
        ('ctx = {"drug": "ciprofloxacin"}', 'ctx = {"drug": "ciprofloxacin", "genetic_data": {"x":"y"}, "infection_data": {"a":"b"}}'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)

    # 3. Handle Guardrails Tests: they either mock or test safety without passing. Let's provide them if needed
    # If the intent is safety_guardrail, Wait! the prompt said IF required fields missing -> guidance, ELSE normal pipeline.
    # Where does guardrails happen? If the user has a safety issue, we should PROBABLY trigger safety BEFORE guidance!
    # Let me check my controller logic... I replaced the lines 78-91! I probably overwrote the guardrail check!
    # Ah!!! I replaced "intercept Explanation requests" but what if there was guardrails?!
    # Let me add the _guardrails instantiation and check in controller.py too in another step.
    
    with open("backend/tests/test_chatbot.py", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch_tests()
