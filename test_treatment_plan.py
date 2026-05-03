#!/usr/bin/env python3
"""
Test Treatment Plan Endpoint
Creates a treatment plan with auto-recommended drugs from classification
"""

import json
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

print("\n" + "="*70)
print("  TREATMENT PLAN TEST - Using Auto-Recommended Drugs")
print("="*70 + "\n")

# Step 1: Create treatment plan with auto-recommended drugs
print("📋 Step 1: Creating Treatment Plan\n")

plan_data = {
    "variants": [
        {
            "gene": "TP53",
            "mutation": "p.R175H frameshift",
            "classification": "PATHOGENIC",
            "acmg_score": 0.95
        },
        {
            "gene": "BRCA1",
            "mutation": "c.68_69delAG frameshift",
            "classification": "PATHOGENIC",
            "acmg_score": 0.95
        }
    ],
    "selected_drugs": [
        {
            "name": "Nutlin-3",
            "interaction": "MDM2 inhibitor",
            "grade": "III"
        },
        {
            "name": "PRIMA-1",
            "interaction": "p53 restoration",
            "grade": "II"
        },
        {
            "name": "Olaparib",
            "interaction": "PARP inhibitor",
            "grade": "I"
        },
        {
            "name": "Rucaparib",
            "interaction": "PARP inhibitor",
            "grade": "I"
        }
    ],
    "created_by": "dr_smith"
}

print("Request Data:")
print(json.dumps(plan_data, indent=2))

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/treatment-plan",
        json=plan_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 201:
        plan_id = result.get("plan_id")
        print(f"\n✅ Treatment Plan Created Successfully!")
        print(f"   Plan ID: {plan_id}")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
    else:
        print(f"\n❌ Failed to create treatment plan")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Step 2: Retrieve all treatment plans
print("\n" + "="*70)
print("📋 Step 2: Retrieving All Treatment Plans\n")

try:
    response = requests.get(
        f"{BASE_URL}/api/v1/treatment-plans",
        params={"limit": 10}
    )
    
    print(f"Status Code: {response.status_code}")
    plans = response.json()
    
    print(f"\nTotal Plans: {plans.get('count')}")
    
    if plans.get('count', 0) > 0:
        print("\n📋 Treatment Plans:")
        for i, plan in enumerate(plans.get('treatment_plans', []), 1):
            print(f"\n  Plan {i}:")
            print(f"    ID: {plan.get('id')}")
            print(f"    Created By: {plan.get('created_by')}")
            print(f"    Status: {plan.get('status')}")
            print(f"    Variants: {len(plan.get('variants', []))}")
            print(f"    Drugs: {len(plan.get('selected_drugs', []))}")
            print(f"    Created At: {plan.get('created_at')}")
        
        print("\n✅ Treatment Plans Retrieved Successfully!")
    else:
        print("\n⚠️  No treatment plans found")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Step 3: Check Audit Log for Treatment Plan Entry
print("\n" + "="*70)
print("📋 Step 3: Checking Audit Log\n")

try:
    response = requests.get(
        f"{BASE_URL}/api/v1/audit-log",
        params={"limit": 50}
    )
    
    logs = response.json()
    
    # Filter for treatment plan entries
    treatment_logs = [log for log in logs.get('audit_logs', []) 
                     if 'TREATMENT_PLAN' in log.get('action', '')]
    
    if treatment_logs:
        print(f"Found {len(treatment_logs)} treatment plan audit entries:\n")
        for log in treatment_logs:
            print(f"  Action: {log.get('action')}")
            print(f"  Resource: {log.get('resource')}")
            print(f"  User: {log.get('user')}")
            print(f"  Timestamp: {log.get('timestamp')}")
            print()
        print("✅ Audit Trail Created Successfully!")
    else:
        print("⚠️  No treatment plan audit entries found")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("="*70)
print("  TEST COMPLETE")
print("="*70 + "\n")
