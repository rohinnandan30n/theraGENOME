import re

text = 'Severe uncontrolled bleeding'
patterns = [
    r'\b(severe\s*bleeding|hemorrhag|uncontrolled\s*bleed|severe.*?bleed)\b',
]

for pattern in patterns:
    result = re.search(pattern, text.lower(), re.IGNORECASE | re.DOTALL)
    print(f'Pattern: {pattern}')
    print(f'Text: {text}')
    print(f'Match: {result}')
    print()

# Test each part
print('Testing individual matches:')
print(f'bleed matches: {bool(re.search(r"bleed", text.lower()))}')
print(f'severe.*bleed matches: {bool(re.search(r"severe.*bleed", text.lower()))}')
print(f'uncontrolled.*bleed matches: {bool(re.search(r"uncontrolled.*bleed", text.lower()))}')
print(f'(severe|uncontrolled).*bleed matches: {bool(re.search(r"(severe|uncontrolled).*bleed", text.lower()))}')
