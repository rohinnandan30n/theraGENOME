import joblib
import numpy as np
from src.config import settings

_model = None

def load_model():
    global _model
    if _model is None:
        _model = joblib.load(settings.TOXICITY_MODEL_PATH)
    return _model

def extract_features(smiles: str) -> list:
    """
    Extract molecular features from SMILES string.
    In production: use RDKit for real molecular descriptors.
    For now: derive simple proxy features from the string.
    """
    length = len(smiles)
    rings = smiles.count("1") + smiles.count("2") + smiles.count("3")
    branches = smiles.count("(")
    oxygens = smiles.upper().count("O")
    nitrogens = smiles.upper().count("N")

    # Map to: [mol_weight_proxy, logP_proxy, hbd, hba, tpsa_proxy]
    features = [
        length * 2.5,
        branches * 0.8 + rings * 0.5,
        oxygens,
        oxygens + nitrogens,
        (oxygens + nitrogens) * 15,
    ]
    return features

def predict_toxicity(smiles: str) -> dict:
    model = load_model()
    features = extract_features(smiles)
    proba = model.predict_proba([features])[0]
    toxic_score = float(proba[1])

    if toxic_score < 0.35:
        risk = "low"
    elif toxic_score < 0.65:
        risk = "medium"
    else:
        risk = "high"

    return {
        "toxicity_score": round(toxic_score, 4),
        "risk_level": risk,
        "features_used": {
            "mol_weight_proxy": round(features[0], 2),
            "logP_proxy": round(features[1], 2),
            "h_bond_donors": features[2],
            "h_bond_acceptors": features[3],
            "tpsa_proxy": features[4],
        }
    }
