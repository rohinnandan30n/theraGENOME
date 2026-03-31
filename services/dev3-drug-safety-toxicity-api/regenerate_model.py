#!/usr/bin/env python3
"""Regenerate 10-feature mock toxicity model."""
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import os

os.makedirs("models", exist_ok=True)

# 10-feature training data
X = np.array([
    [180.2, 1.2, 1, 4, 2, 1, 13, 61.4, 0, 0],
    [152.1, 0.8, 2, 4, 1, 0, 8, 87.3, 0, 0],
    [194.2, 0.2, 0, 3, 1, 2, 14, 48.9, 0, 0],
    [206.3, 3.9, 1, 2, 4, 2, 13, 37.3, 0, 0],
    [250.4, 2.1, 0, 5, 2, 1, 16, 65.2, 0, 0],
    [165.0, 1.5, 3, 3, 1, 1, 11, 72.1, 0, 0],
    [310.2, 2.8, 2, 6, 3, 2, 20, 91.5, 0, 0],
    [275.3, 1.9, 1, 4, 2, 2, 18, 58.4, 0, 0],
    [520.5, 5.9, 1, 8, 6, 3, 38, 120.1, 0, 0],
    [600.2, 7.2, 2, 9, 7, 2, 42, 145.3, 0, 0],
    [480.1, 6.1, 0, 7, 5, 4, 35, 115.2, 3, 0],
    [410.3, 5.8, 1, 6, 4, 3, 30, 108.5, 0, 2],
    [650.4, 7.5, 0, 10, 8, 3, 48, 152.0, 2, 0],
    [380.0, 6.2, 3, 8, 5, 2, 28, 130.2, 1, 1],
    [340.2, 3.5, 2, 5, 3, 2, 22, 85.1, 0, 0],
    [420.1, 4.8, 1, 6, 4, 1, 32, 102.3, 1, 0],
    [290.0, 2.9, 2, 4, 2, 2, 17, 76.2, 0, 0],
    [550.5, 6.5, 0, 7, 6, 3, 40, 125.0, 2, 1],
    [200.1, 2.0, 3, 3, 1, 1, 12, 68.9, 0, 0],
    [380.4, 5.2, 1, 7, 5, 2, 29, 110.5, 1, 0],
])

y = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1])

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1))
])

pipeline.fit(X, y)
joblib.dump(pipeline, "models/toxicity_model.joblib")

print("✅ 10-Feature Mock Model Generated!")
print("   Features: 10 (MW, LogP, HBD, HBA, Rotatable, Aromatic, Heavy, PSA, Halogens, Sulfur)")
print("   Samples: 20 (8 safe + 6 toxic + 6 mixed)")
print("   Trees: 100, Max Depth: 10")
print("   Saved: models/toxicity_model.joblib")
