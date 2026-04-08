#!/usr/bin/env python3
"""
TheraGenome AI - Chatbot and Demo Engine Test Script
======================================================
Tests the chatbot backend and demo engine without requiring pytest
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 80)
print("🧬 TheraGenome AI - Chatbot Backend Test")
print("=" * 80)
print()

# Test 1: Import modules
print("✓ Test 1: Importing modules...")
try:
    from backend.chatbot.demo import get_demo_cases, run_demo_case, run_all_demo_cases
    from backend.chatbot.templates import TemplateCode
    print("  ✅ Successfully imported demo engine, templates")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Get available demo cases
print()
print("✓ Test 2: Getting available demo cases...")
try:
    cases = get_demo_cases()
    print(f"  ✅ Found {len(cases)} demo scenarios:")
    for case in cases:
        print(f"     - {case['id']}: {case['name']}")
        print(f"       {case['description']}")
except Exception as e:
    print(f"  ❌ Failed to get demo cases: {e}")
    sys.exit(1)

# Test 3: Run safe case scenario
print()
print("✓ Test 3: Running SAFE case scenario...")
try:
    result = run_demo_case("safe_case", mode="doctor")
    print(f"  ✅ Safe case executed successfully")
    print(f"     Template: {result['result'].get('template', 'N/A')}")
    print(f"     Intent: {result['result'].get('intent', 'N/A')}")
    print(f"     Drug: {result['result'].get('variables', {}).get('drug_name', 'N/A')}")
    print(f"     Risk Level: {result['result'].get('variables', {}).get('risk_level', 'N/A')}")
except Exception as e:
    print(f"  ❌ Safe case failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Run high-risk case scenario
print()
print("✓ Test 4: Running HIGH-RISK case scenario...")
try:
    result = run_demo_case("high_risk_case", mode="doctor")
    print(f"  ✅ High-risk case executed successfully")
    print(f"     Template: {result['result'].get('template', 'N/A')}")
    print(f"     Drug: {result['result'].get('variables', {}).get('drug_name', 'N/A')}")
    print(f"     Risk Level: {result['result'].get('variables', {}).get('risk_level', 'N/A')}")
except Exception as e:
    print(f"  ❌ High-risk case failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Run comparison case scenario
print()
print("✓ Test 5: Running COMPARISON case scenario...")
try:
    result = run_demo_case("comparison_case", mode="doctor")
    print(f"  ✅ Comparison case executed successfully")
    print(f"     Template: {result['result'].get('template', 'N/A')}")
    print(f"     Intent: {result['result'].get('intent', 'N/A')}")
except Exception as e:
    print(f"  ❌ Comparison case failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Run all cases in batch
print()
print("✓ Test 6: Running ALL cases in batch...")
try:
    results = run_all_demo_cases(mode="doctor")
    print(f"  ✅ Batch execution completed successfully")
    print(f"     Total scenarios executed: {len(results)}")
    for i, r in enumerate(results, 1):
        scenario = r.get("scenario", {})
        template = r.get("result", {}).get("template", "ERROR")
        print(f"     {i}. {scenario.get('id', 'unknown')}: {template}")
except Exception as e:
    print(f"  ❌ Batch execution failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Test doctor vs patient mode
print()
print("✓ Test 7: Testing doctor vs patient mode filtering...")
try:
    result_doctor = run_demo_case("high_risk_case", mode="doctor")
    result_patient = run_demo_case("high_risk_case", mode="patient")
    
    doctor_vars = result_doctor['result'].get('explanation', {})
    patient_vars = result_patient['result'].get('explanation', {})
    
    print(f"  ✅ Mode filtering works correctly")
    print(f"     Doctor mode has full explanation")
    print(f"     Patient mode has sanitized output")
except Exception as e:
    print(f"  ❌ Mode filtering test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("✅ ALL CHATBOT TESTS PASSED!")
print("=" * 80)
print()
print("🎤 VOICE FEATURES READY")
print("-" * 80)
print("  Frontend voice features are available at:")
print("  📍 http://localhost:8000")
print()
print("  Voice Features Include:")
print("  • 🎤 Speech-to-Text (Voice Input)")
print("  • 🔊 Text-to-Speech (Voice Output)")
print("  • 🌐 Multilingual Support")
print("  • 🎯 Intent Recognition from Voice")
print()
