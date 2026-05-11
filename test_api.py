import requests
import json

test_data = {
    'text': '''PATIENT: Sarah Johnson
DOB: 1975-04-22
DATE: 2026-04-09

GENETIC MARKERS:
- CYP2D6: *1/*4 (Intermediate Metabolizer)
- CYP2C19: *1/*2 (Intermediate Metabolizer)  
- CYP3A4: Normal function
- MTHFR: C677T heterozygous
- SLCO1B1: c.521T>C (Normal)
- TPMT: Normal activity

LAB RESULTS:
- Depression Severity Score: 28
- Blood Pressure: 145/92 mmHg
- HR: 78 bpm''',
    'mode': 'doctor',
    'report_type': 'pasted_text'
}

try:
    response = requests.post('http://localhost:8000/api/v1/reports/analyze-text', json=test_data, timeout=10)
    result = response.json()
    pharm = result.get('data', {}).get('analysis', {}).get('pharmacogenomics', {})
    
    print('✅ GENETIC ANALYSIS RESULTS:')
    print('━' * 60)
    print('Genetic Markers Detected:', pharm.get('genetic_markers_detected'))
    print('CYP Profile:', pharm.get('cyp_profile'))
    print('Efficiency:', pharm.get('metabolism_efficiency'))
    print('Risk Level:', pharm.get('drug_interaction_risk'))
    print()
    print('📋 Drug Recommendations:', len(pharm.get('specific_recommendations', [])))
    print('━' * 60)
    print()
    for i, rec in enumerate(pharm.get('specific_recommendations', [])[:5], 1):
        drug = rec.get('specific_drug', rec.get('category', 'Unknown'))
        print(f'{i}. {drug}')
        print(f'   Rank: {rec.get("rank", "N/A")}')
        print(f'   Initial: {rec.get("initial_dose", "N/A")}')
        print(f'   Target: {rec.get("target_dose", "N/A")}')
        print(f'   Genetic Score: {rec.get("genetic_score", "N/A")}')
        print()
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
