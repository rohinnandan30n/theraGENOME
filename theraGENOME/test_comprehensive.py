import requests
import json

# Test 1: Non-genetic blood work report
test_1_data = {
    'text': '''PATIENT: John Doe
DATE: 2026-04-09

COMPLETE BLOOD COUNT:
WHITE BLOOD CELL: 12.5 k/uL (Reference: 4.5-11.0) - HIGH
RED BLOOD CELL: 4.8 M/uL (Reference: 4.5-5.9)
HEMOGLOBIN: 14.5 g/dL (Reference: 13.0-17.0)
HEMATOCRIT: 43% (Reference: 41-53%)

METABOLIC PANEL:
GLUCOSE: 105 mg/dL (Reference: 70-100 fasting) - HIGH
BUN: 20 mg/dL (Reference: 7-20)
CREATININE: 1.0 mg/dL (Reference: 0.7-1.3)

BACTERIAL CULTURE:
- Staphylococcus aureus: DETECTED
- Sensitivity to Ampicillin: RESISTANT
- Sensitivity to Amoxicillin: RESISTANT
- Sensitivity to Penicillin: RESISTANT
- Sensitivity to Cephalosporins: SENSITIVE''',
    'mode': 'doctor',
    'report_type': 'pasted_text'
}

# Test 2: Genetic markers report
test_2_data = {
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

def test_api(test_name, data):
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print('='*70)
    try:
        response = requests.post('http://localhost:8000/api/v1/reports/analyze-text', json=data, timeout=10)
        if response.status_code != 200:
            print(f"❌ ERROR: Status {response.status_code}")
            print(response.text)
            return
        
        result = response.json()
        if not result.get('success'):
            print(f"❌ API returned success=false")
            print(json.dumps(result, indent=2))
            return
        
        print("✅ SUCCESS - Status 200")
        analysis = result.get('data', {}).get('analysis', {})
        
        # Check all sections
        print("\n📊 SECTIONS AVAILABLE:")
        sections = {
            'summary': analysis.get('summary'),
            'test_results': analysis.get('test_results'),
            'diseases': analysis.get('diseases'),
            'genetic': analysis.get('pharmacogenomics'),
            'resistance': analysis.get('antibiotic_resistance'),
            'toxicity': analysis.get('drug_toxicity')
        }
        
        for section, data_obj in sections.items():
            if data_obj:
                print(f"  ✓ {section.upper()}: Present")
                if isinstance(data_obj, dict):
                    print(f"      Keys: {list(data_obj.keys())[:5]}...")
                elif isinstance(data_obj, list):
                    print(f"      Items: {len(data_obj)} records")
            else:
                print(f"  ✗ {section.upper()}: Missing/Null")
        
        # Check genetic data specifically
        print("\n🧬 GENETIC DATA DETAIL:")
        if analysis.get('pharmacogenomics'):
            pharm = analysis['pharmacogenomics']
            print(f"  Markers Detected: {pharm.get('genetic_markers_detected')}")
            print(f"  CYP Profile: {pharm.get('cyp_profile')}")
            print(f"  Efficiency: {pharm.get('metabolism_efficiency')}")
            print(f"  Risk: {pharm.get('drug_interaction_risk')}")
            print(f"  Recommendations: {len(pharm.get('specific_recommendations', []))} items")
        else:
            print("  ⚠️ Genetic data not returned")
        
        # Check resistance data
        print("\n🦠 RESISTANCE DATA DETAIL:")
        if analysis.get('antibiotic_resistance'):
            resist = analysis['antibiotic_resistance']
            print(f"  Infections Detected: {len(resist.get('infections', []))} items")
            print(f"  Susceptibility Data: {len(resist.get('susceptibility_data', []))} items")
            print(f"  Recommendations: {len(resist.get('antibiotic_recommendations', []))} items")
        else:
            print("  ⚠️ Resistance data not returned")
        
        # Check toxicity data
        print("\n💊 TOXICITY DATA DETAIL:")
        if analysis.get('drug_toxicity'):
            tox = analysis['drug_toxicity']
            print(f"  Warnings: {len(tox.get('toxicity_warnings', []))} items")
            print(f"  Safe Drugs: {len(tox.get('safe_drugs', []))} items")
            print(f"  Drug Interactions: {len(tox.get('drug_interactions', []))} items")
        else:
            print("  ⚠️ Toxicity data not returned")
        
        # Show full response structure
        print("\n📋 FULL RESPONSE KEYS:")
        print(f"  {json.dumps(result.get('data', {}), indent=2)[:500]}...")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

# Run tests
print("\n" + "="*70)
print("COMPREHENSIVE DATA FETCHING TEST SUITE")
print("="*70)

test_api("Test 1: Blood Work + Bacterial Infection (No Genetic)", test_1_data)
test_api("Test 2: Genetic Markers + Depression (With Genetic)", test_2_data)

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
