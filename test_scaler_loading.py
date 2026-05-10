#!/usr/bin/env python3
"""Diagnostic: Check scaler loading in classifier"""

import logging
import json
import os
from src.ml.model_manager import get_registry
from src.ml.classifier import PathogenicityClassifier

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("SCALER LOADING DIAGNOSTIC")
print("="*80 + "\n")

# Check registry metadata
registry = get_registry()
print("Registry metadata entries:")
for model_id, metadata in registry.model_metadata.items():
    print(f"\n  Model ID: {model_id}")
    print(f"    Has scaler_path: {'scaler_path' in metadata}")
    if 'scaler_path' in metadata:
        print(f"    Scaler path: {metadata['scaler_path']}")
        print(f"    File exists: {os.path.exists(metadata['scaler_path'])}")
    print(f"    Full metadata keys: {list(metadata.keys())}")

# Check JSON files
print("\n" + "-"*80)
print("JSON Metadata Files:")
for filename in os.listdir('./models'):
    if filename.endswith('_metadata.json'):
        filepath = os.path.join('./models', filename)
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"\n  {filename}:")
        print(f"    Has scaler_path: {'scaler_path' in data}")
        if 'scaler_path' in data:
            print(f"    Scaler path: {data['scaler_path']}")

# Now test classifier loading
print("\n" + "-"*80)
print("Classifier Loading Test:")
try:
    classifier = PathogenicityClassifier(default_version='v1')
    print(f"  Current model loaded: {classifier.current_version}")
    print(f"  Has scaler: {classifier.current_scaler is not None}")
    if classifier.current_scaler:
        print(f"  Scaler type: {type(classifier.current_scaler)}")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80 + "\n")
