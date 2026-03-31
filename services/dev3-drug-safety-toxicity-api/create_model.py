import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import os

os.makedirs("models", exist_ok=True)

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(n_estimators=10, random_state=42))
])

X = np.array([
    [180, 1.2, 2, 3, 45],
    [250, 2.5, 1, 4, 60],
    [400, 4.8, 0, 6, 90],
    [520, 5.9, 1, 8, 120],
    [600, 7.2, 2, 9, 140],
    [150, 0.8, 3, 2, 30],
    [480, 6.1, 0, 7, 110],
    [320, 3.4, 1, 5, 75],
])
y = [0, 0, 1, 1, 1, 0, 1, 1]

pipeline.fit(X, y)
joblib.dump(pipeline, "models/toxicity_model.joblib")
print("✅ Mock toxicity model saved!")
