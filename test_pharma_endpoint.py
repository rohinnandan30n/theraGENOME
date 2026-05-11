#!/usr/bin/env python3
"""Test the pharmacogenomics report analyzer endpoint."""

import requests
import json

# Read the sample patient report
with open('sample_patient_james_mitchell.txt', 'r', encoding='utf-8') as f:
    sample_report = f.read()

# Test the analyze-pharma endpoint
url = "http://localhost:8000/api/v1/reports/analyze-pharma"

payload = {
    "text": sample_report,
    "mode": "doctor",
    "report_type": "pharmacogenomics"
}

print("Testing /api/v1/reports/analyze-pharma endpoint...")
print("=" * 80)

try:
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✓ SUCCESS! Endpoint returned 200 OK")
        print("\nResponse Summary:")
        print(f"  - Mode: {data.get('mode')}")
        print(f"  - Report Type: {data.get('report_type')}")
        print(f"  - Patient Name: {data.get('patient_name')}")
        print(f"  - Date: {data.get('date_of_report')}")
        print(f"  - Confidence: {data.get('confidence')}")
        print(f"  - Message: {data.get('message')}")
        
        if 'data' in data:
            print(f"\n  - Tests Found: {len(data['data'].get('tests', []))}")
            if 'analysis' in data['data']:
                print(f"  - Critical Findings: {len(data['data']['analysis'].get('critical_findings', []))}")
                print(f"  - Drug Recommendations: {len(data['data']['analysis'].get('drug_recommendations', []))}")
        
        print("\nFull Response:")
        print(json.dumps(data, indent=2)[:1000] + "...\n")
    else:
        print(f"✗ ERROR! Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"✗ Connection Error: {e}")
    print("\nMake sure the backend is running at http://localhost:8000")

print("=" * 80)
