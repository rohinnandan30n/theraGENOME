"""
Test script to analyze reports via the running API
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test if API is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"[OK] Backend Health: {response.json()}\n")
        return True
    except Exception as e:
        print(f"[FAILED] Backend Error: {e}\n")
        return False

def test_drug_analysis():
    """Test drug analysis endpoint"""
    print("=" * 80)
    print("TEST 1: Drug Toxicity Analysis")
    print("=" * 80)
    
    payload = {
        "input": "Analyze the toxicity of amoxicillin for liver function",
        "mode": "doctor",
        "context": {
            "drug": "amoxicillin",
            "organ": "liver"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chatbot/query",
            json=payload,
            timeout=10
        )
        result = response.json()
        print(json.dumps(result, indent=2))
        print("\n")
        return result
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None

def test_compare_drugs():
    """Test drug comparison"""
    print("=" * 80)
    print("TEST 2: Drug Comparison")
    print("=" * 80)
    
    payload = {
        "input": "Compare penicillin vs amoxicillin for UTI",
        "mode": "doctor",
        "context": {
            "drugs": ["penicillin", "amoxicillin"],
            "indication": "urinary tract infection"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chatbot/query",
            json=payload,
            timeout=10
        )
        result = response.json()
        print(json.dumps(result, indent=2))
        print("\n")
        return result
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None

def test_genetic_data():
    """Test genetic data processing"""
    print("=" * 80)
    print("TEST 3: Genetic Data Input")
    print("=" * 80)
    
    payload = {
        "input": "Upload my CYP2D6 and SLCO1B1 genetic markers",
        "mode": "patient",
        "context": {
            "genetic_data": {
                "markers": ["CYP2D6", "SLCO1B1", "UGT1A1"],
                "phenotypes": {
                    "CYP2D6": "ultra-rapid metabolizer",
                    "SLCO1B1": "reduced function",
                    "UGT1A1": "Gilbert syndrome"
                }
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chatbot/query",
            json=payload,
            timeout=10
        )
        result = response.json()
        print(json.dumps(result, indent=2))
        print("\n")
        return result
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None

def test_safety_guardrails():
    """Test safety guardrails"""
    print("=" * 80)
    print("TEST 4: Safety Guardrails - Emergency Detection")
    print("=" * 80)
    
    payload = {
        "input": "I have severe chest pain and can't breathe",
        "mode": "doctor",
        "context": {}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chatbot/query",
            json=payload,
            timeout=10
        )
        result = response.json()
        print(json.dumps(result, indent=2))
        print("\n")
        return result
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None

def test_patient_mode():
    """Test patient mode filtering"""
    print("=" * 80)
    print("TEST 5: Patient Mode (Simplified Output)")
    print("=" * 80)
    
    payload = {
        "input": "Is warfarin safe for me?",
        "mode": "patient",
        "context": {
            "user_profile": {
                "age": 65,
                "conditions": ["hypertension", "atrial fibrillation"]
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chatbot/query",
            json=payload,
            timeout=10
        )
        result = response.json()
        print(json.dumps(result, indent=2))
        print("\n")
        return result
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None

def main():
    print("\n")
    print("+" + "=" * 78 + "+")
    print("|" + " " * 78 + "|")
    print("|" + "  THERAGENOME AI - BACKEND ANALYSIS TEST SUITE".center(78) + "|")
    print("|" + " " * 78 + "|")
    print("+" + "=" * 78 + "+\n")
    
    # Test health
    if not test_health():
        print("[WARN] Backend is not responding. Make sure it's running on port 8000")
        return
    
    # Run tests
    test_drug_analysis()
    test_compare_drugs()
    test_genetic_data()
    test_safety_guardrails()
    test_patient_mode()
    
    print("=" * 80)
    print("*** ANALYSIS COMPLETE ***")
    print("=" * 80)

if __name__ == "__main__":
    main()
