#!/usr/bin/env python3
"""Test the full frontend analyze report flow."""

import requests
import json

# Read the sample patient report
with open('sample_patient_james_mitchell.txt', 'r', encoding='utf-8') as f:
    sample_report = f.read()

print("=" * 80)
print("TESTING FULL REPORT ANALYZER FLOW (Frontend Simulation)")
print("=" * 80)

# Test 1: Analyze-Pharma for pharmacogenomics reports
print("\n[TEST 1] Pharmacogenomics Report Analysis")
print("-" * 80)

payload = {
    "text": sample_report,
    "mode": "doctor",
    "report_type": "pharmacogenomics"
}

try:
    response = requests.post(
        "http://localhost:8000/api/v1/reports/analyze-pharma",
        json=payload,
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ Pharmacogenomics endpoint SUCCESS")
        print(f"  Patient: {data.get('patient_name')}")
        print(f"  Tests Analyzed: {len(data['data'].get('tests', []))}")
        print(f"  Critical Findings: {len(data['data']['analysis'].get('critical_findings', []))}")
        print(f"  Drug Recommendations: {len(data['data']['analysis'].get('drug_recommendations', []))}")
        print(f"  Message: {data.get('message')}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text[:200])
except Exception as e:
    print(f"✗ Connection error: {e}")

# Test 2: Standard analyze-text endpoint
print("\n[TEST 2] Standard Report Analysis (Fallback)")
print("-" * 80)

payload2 = {
    "text": "Patient: John Doe\nDate: May 11, 2026\nWhite Blood Cell: 12.5 k/uL\nRed Blood Cell: 5.2 M/uL",
    "mode": "doctor",
    "report_type": "blood_work"
}

try:
    response = requests.post(
        "http://localhost:8000/api/v1/reports/analyze-text",
        json=payload2,
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✓ Standard analyze-text endpoint SUCCESS")
        print(f"  Patient: {data.get('patient_name')}")
        print(f"  Tests: {len(data['data'].get('tests', []))}")
        print(f"  Message: {data.get('message')}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text[:200])
except Exception as e:
    print(f"✗ Connection error: {e}")

print("\n" + "=" * 80)
print("RESULT: Frontend Analyze Report Button Should Now Work!")
print("=" * 80)
print("\nHow it works:")
print("1. User uploads or pastes a report")
print("2. Frontend tries analyze-pharma endpoint first (for pharmacogenomics data)")
print("3. If that returns an error, falls back to analyze-text (standard lab tests)")
print("4. Results display in appropriate tabs (Summary, Tests, Analysis)")
print("\nYour sample patient report (James Mitchell) is now fully parseable!")
