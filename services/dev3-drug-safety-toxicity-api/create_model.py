"""
Generate a mock toxicity prediction model for development/testing.

This creates a RandomForest model trained on 10 molecular descriptors:
1. Molecular Weight (MW)
2. LogP (Hydrophobicity)
3. H-Bond Donors (HBD)
4. H-Bond Acceptors (HBA)
5. Rotatable Bonds
6. Aromatic Rings
7. Heavy Atoms
8. Polar Surface Area (PSA)
9. Halogens Count
10. Sulfur Atoms

The model uses a simple heuristic: compounds with higher MW, LogP, and HBD
are more likely to be toxic (class 1). Low MW, typical LogP, and moderate 
donors are generally safe (class 0).

IMPORTANT: This is a mock model for development only. Production models
should be trained on actual toxicity databases (e.g., Tox21, PubChem).
"""

import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import os

os.makedirs("models", exist_ok=True)

# Training data: 10 features per sample
# Features: [MW, LogP, HBD, HBA, Rotatable, Aromatic, Heavy, PSA, Halogens, Sulfur]
X = np.array([
    # Low toxicity (class 0) - typical drug-like compounds
    [180.2, 1.2, 1, 4, 2, 1, 13, 61.4, 0, 0],  # Aspirin-like
    [152.1, 0.8, 2, 4, 1, 0, 8, 87.3, 0, 0],   # Acetaminophen-like
    [194.2, 0.2, 0, 3, 1, 2, 14, 48.9, 0, 0],  # Caffeine-like
    [206.3, 3.9, 1, 2, 4, 2, 13, 37.3, 0, 0],  # Ibuprofen-like
    [250.4, 2.1, 0, 5, 2, 1, 16, 65.2, 0, 0],  # Generic safe compound
    [165.0, 1.5, 3, 3, 1, 1, 11, 72.1, 0, 0],  # Safe with H-bonds
    [310.2, 2.8, 2, 6, 3, 2, 20, 91.5, 0, 0],  # Moderate MW, safe
    [275.3, 1.9, 1, 4, 2, 2, 18, 58.4, 0, 0],  # Typical pharma

    # High toxicity (class 1) - problematic compounds
    [520.5, 5.9, 1, 8, 6, 3, 38, 120.1, 0, 0],  # Very high MW & LogP
    [600.2, 7.2, 2, 9, 7, 2, 42, 145.3, 0, 0],  # Extremely lipophilic
    [480.1, 6.1, 0, 7, 5, 4, 35, 115.2, 3, 0],  # Multiple halogens
    [410.3, 5.8, 1, 6, 4, 3, 30, 108.5, 0, 2],  # High MW + sulfur
    [650.4, 7.5, 0, 10, 8, 3, 48, 152.0, 2, 0],  # Extreme properties
    [380.0, 6.2, 3, 8, 5, 2, 28, 130.2, 1, 1],  # High LogP + donors
    
    # Intermediate cases
    [340.2, 3.5, 2, 5, 3, 2, 22, 85.1, 0, 0],
    [420.1, 4.8, 1, 6, 4, 1, 32, 102.3, 1, 0],
    [290.0, 2.9, 2, 4, 2, 2, 17, 76.2, 0, 0],
    [550.5, 6.5, 0, 7, 6, 3, 40, 125.0, 2, 1],
    [200.1, 2.0, 3, 3, 1, 1, 12, 68.9, 0, 0],
    [380.4, 5.2, 1, 7, 5, 2, 29, 110.5, 1, 0],
])

# Labels: 0 = low toxicity (safe), 1 = high toxicity (dangerous)
y = np.array([0, 0, 0, 0, 0, 0, 0, 0,  # 8 safe compounds
              1, 1, 1, 1, 1, 1,         # 6 toxic compounds
              0, 1, 0, 1, 0, 1])        # 6 mixed cases

# Create and train model
pipeline = Pipeline([
    ("scaler", StandardScaler()),  # Normalize features for better learning
    ("clf", RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1
    ))
])

pipeline.fit(X, y)
joblib.dump(pipeline, "models/toxicity_model.joblib")

print("\n" + "="*60)
print("✅ Mock Toxicity Model Generated Successfully!")
print("="*60)
print(f"Training samples: {len(X)}")
print(f"Features per sample: {X.shape[1]}")
print(f"Feature names: MW, LogP, HBD, HBA, Rotatable, Aromatic, Heavy, PSA, Halogens, Sulfur")
print(f"Classes: 0 (Low Toxicity), 1 (High Toxicity)")
print(f"Model type: Random Forest ({pipeline.named_steps['clf'].n_estimators} trees)")
print(f"Saved to: models/toxicity_model.joblib")
print("="*60 + "\n")
