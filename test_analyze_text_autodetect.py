#!/usr/bin/env python3
"""Test that analyze_text auto-detects pharmacogenomics reports and routes correctly."""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Load the sample pharmacogenomics report
with open("sample_patient_james_mitchell.txt", "r", encoding="utf-8") as f:
    pharma_text = f.read()

# Test 1: Call analyze_text with pharmacogenomics report
print("=" * 80)
print("Testing /api/v1/reports/analyze-text with pharmacogenomics report...")
print("=" * 80)

payload = {
    "text": pharma_text,
    "mode": "doctor",
    "report_type": "pasted_text"
}

response = requests.post(f"{BASE_URL}/reports/analyze-text", json=payload)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"\n✓ SUCCESS! Endpoint returned 200 OK")
    print(f"\nResponse Summary:")
    print(f"  - Mode: {result.get('mode')}")
    print(f"  - Report Type: {result.get('report_type')}")
    print(f"  - Patient Name: {result.get('patient_name')}")
    print(f"  - Date: {result.get('date_of_report')}")
    print(f"  - Confidence: {result.get('confidence')}")
    print(f"  - Message: {result.get('message')}")
    
    tests = result.get('data', {}).get('tests', [])
    print(f"\n  - Tests Found: {len(tests)}")
    
    if len(tests) > 0:
        print("\nTests extracted:")
        for test in tests[:3]:
            print(f"  {test['test_name']}: {test['value']} ({test['abnormality']})")
        if len(tests) > 3:
            print(f"  ... and {len(tests) - 3} more")
    else:
        print("  ⚠️ WARNING: No tests extracted!")
    
    print(f"\nFull Response:")
    print(json.dumps(result, indent=2)[:1000])
else:
    print(f"✗ FAILED with status {response.status_code}")
    print(f"Response: {response.text[:500]}")
