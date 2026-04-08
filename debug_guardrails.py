import re

query = "Which drug is better: amoxicillin vs doxycycline?"
patterns = [
    r"\b(what|which|give|prescribe).{0,30}(without|no|alone|myself).{0,20}(doctor|physician|supervision|nurse|pharmacist)",
    r"\b(can\s*i\s*(take|use|give)).{0,30}(without|no|alone|myself).{0,20}(doctor|physician|supervision|consultation)",
    r"\b(should|can|may|could)\s*(i|you)\s*(take|use).{0,20}\b(without|no)\b.{0,20}(doctor|physician|consultation|prescription)",
]

text = query.lower()

for i, pattern in enumerate(patterns):
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    print(f"Pattern {i}: {pattern[:60]}...")
    print(f"Match: {match}")
    print()

# Also check final logic in function
drug_names = ["amoxicillin", "ciprofloxacin", "warfarin", "metformin", "tramadol", "codeine"]
has_drug = any(drug in text for drug in drug_names)
print(f"Has drug: {has_drug}")

has_pattern = re.search(r"\b(what\s*(drug|medicine)|which\s*(drug|medicine)|give\s*me|prescribe)\b", text)
print(f"Has which/what drug pattern: {bool(has_pattern)}")
