from pydantic import BaseModel
from typing import Optional

class ToxicityPredictRequest(BaseModel):
    compound_smiles: str
    patient_id: Optional[str] = None

class ToxicityPredictResponse(BaseModel):
    compound_smiles: str
    toxicity_score: float
    risk_level: str
    shap_values: Optional[dict] = None

class PGxResponse(BaseModel):
    gene: str
    drug: str
    recommendation: str
    evidence_level: str

class DDIRequest(BaseModel):
    drug_a: str
    drug_b: str

class DDIResponse(BaseModel):
    drug_a: str
    drug_b: str
    interaction_type: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
