#!/usr/bin/env python3
from src.ml.model_manager import get_registry

registry = get_registry()
print("\n=== MODEL PERFORMANCE METRICS ===\n")
for model in registry.list_models('pathogenicity'):
    print(f"{model['name']}:{model['version']}")
    print(f"  Accuracy:    {model['performance'].get('accuracy', 'N/A')}")
    print(f"  Sensitivity: {model['performance'].get('sensitivity', 'N/A')}")
    print(f"  Specificity: {model['performance'].get('specificity', 'N/A')}")
    print(f"  AUC-ROC:     {model['performance'].get('auc_roc', 'N/A')}")
    print()
