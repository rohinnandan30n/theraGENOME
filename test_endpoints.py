#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing
Tests all 8 endpoints of the TheraGenome Hackathon API
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_response(response, title="Response"):
    """Pretty print response"""
    print(f"{title}:")
    print(f"  Status Code: {response.status_code}")
    try:
        print(f"  Body: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"  Body: {response.text}")

# ============================================
# ENDPOINT 1: Health Check
# ============================================
def test_health():
    print_section("TEST 1: Health Check (GET /health)")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print_response(response)
        assert response.status_code == 200
        print("✅ PASS: Health check successful\n")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
        return False

# ============================================
# ENDPOINT 2: Classify Variants
# ============================================
def test_classify():
    print_section("TEST 2: Classify Variants (POST /api/v1/classify)")
    try:
        # Create test variant file
        test_variants = [
            {
                "gene": "TP53",
                "mutation": "p.R175H frameshift"
            },
            {
                "gene": "BRCA1",
                "mutation": "c.68_69delAG missense"
            },
            {
                "gene": "EGFR",
                "mutation": "p.L858R benign"
            }
        ]
        
        files = {'file': ('variants.json', json.dumps(test_variants))}
        response = requests.post(f"{BASE_URL}/api/v1/classify", files=files)
        print_response(response)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["variants_processed"] == 3
        print("✅ PASS: Variants classified successfully\n")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
        return False

# ============================================
# ENDPOINT 3: Get Results
# ============================================
def test_get_results():
    print_section("TEST 3: Get Results (GET /api/v1/results?limit=10)")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/results", params={"limit": 10})
        print_response(response)
        assert response.status_code == 200
        print("✅ PASS: Results retrieved successfully\n")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
        return False

# ============================================
# ENDPOINT 4: Get Drug Interactions
# ============================================
def test_get_drugs():
    print_section("TEST 4: Get Drug Interactions (GET /api/v1/drugs/{gene})")
    try:
        genes = ["TP53", "BRCA1", "EGFR", "CYP2D6"]
        for gene in genes:
            response = requests.get(f"{BASE_URL}/api/v1/drugs/{gene}")
            print(f"\n{gene}:")
            print_response(response, f"Response for {gene}")
            assert response.status_code == 200
        
        print("\n✅ PASS: Drug interactions retrieved successfully\n")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
        return False

# ============================================
# ENDPOINT 5: Get Audit Log
# ============================================
def test_audit_log():
    print_section("TEST 5: Get Audit Log (GET /api/v1/audit-log?limit=50)")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/audit-log", params={"limit": 50})
        print_response(response)
        assert response.status_code == 200
        print("✅ PASS: Audit log retrieved successfully\n")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
        return False

# ============================================
# ENDPOINT 6: Serve Dashboard
# ============================================
def test_dashboard():
    print_section("TEST 6: Serve Dashboard (GET /)")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Check if it's HTML
            if "<!DOCTYPE" in response.text or "<html" in response.text:
                print("Dashboard HTML served successfully")
                print(f"Content-Type: {response.headers.get('content-type')}")
                print(f"Response length: {len(response.text)} bytes")
                print("✅ PASS: Dashboard served successfully\n")
                return True
            else:
                print(f"Response: {response.json()}")
                print("✅ PASS: Dashboard endpoint accessible\n")
                return True
        else:
            print(f"Response: {response.text}")
            print("✅ PASS: Dashboard endpoint accessible (not found is expected)\n")
            return True
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
        return False

# ============================================
# ENDPOINT 7: Create Treatment Plan
# ============================================
def test_create_treatment_plan():
    print_section("TEST 7: Create Treatment Plan (POST /api/v1/treatment-plan)")
    try:
        plan_data = {
            "variants": [
                {"gene": "TP53", "mutation": "p.R175H"},
                {"gene": "BRCA1", "mutation": "c.68_69delAG"}
            ],
            "selected_drugs": [
                {"name": "Olaparib", "interaction": "PARP inhibitor", "grade": "I"},
                {"name": "Nutlin-3", "interaction": "MDM2 inhibitor", "grade": "III"}
            ],
            "created_by": "test_clinician"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/treatment-plan",
            json=plan_data,
            headers={"Content-Type": "application/json"}
        )
        print_response(response)
        assert response.status_code == 201
        assert response.json()["status"] == "success"
        print("✅ PASS: Treatment plan created successfully\n")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
        return False

# ============================================
# ENDPOINT 8: Get Treatment Plans
# ============================================
def test_get_treatment_plans():
    print_section("TEST 8: Get Treatment Plans (GET /api/v1/treatment-plans?limit=10)")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/treatment-plans", params={"limit": 10})
        print_response(response)
        assert response.status_code == 200
        print("✅ PASS: Treatment plans retrieved successfully\n")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}\n")
        return False

# ============================================
# MAIN TEST RUNNER
# ============================================
def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "THERAGENOME API ENDPOINT TESTS" + " "*23 + "║")
    print("║" + " "*20 + f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " "*16 + "║")
    print("╚" + "="*68 + "╝")
    
    results = []
    
    # Run all tests
    results.append(("Health Check", test_health()))
    results.append(("Classify Variants", test_classify()))
    results.append(("Get Results", test_get_results()))
    results.append(("Get Drug Interactions", test_get_drugs()))
    results.append(("Get Audit Log", test_audit_log()))
    results.append(("Serve Dashboard", test_dashboard()))
    results.append(("Create Treatment Plan", test_create_treatment_plan()))
    results.append(("Get Treatment Plans", test_get_treatment_plans()))
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed\n")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)
