from fastapi import APIRouter, HTTPException
from src.api.schemas import ToxicityPredictRequest, ToxicityPredictResponse, DDIRequest, DDIResponse
from src.external_apis.faers_api import get_adverse_events
from src.external_apis.pharmgkb_api import get_pgx_recommendation
from src.external_apis.drugbank_api import check_drug_interaction
from src.ml.toxicity_model import predict_toxicity

router = APIRouter()

@router.post("/predict-toxicity")
async def predict_toxicity_endpoint(payload: ToxicityPredictRequest):
    """Predict toxicity for a compound given its SMILES string."""
    try:
        result = predict_toxicity(payload.compound_smiles)
        return {
            "compound_smiles": payload.compound_smiles,
            "patient_id": payload.patient_id,
            **result,
            "note": "Mock model — replace with trained toxicity model in production."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@router.get("/pgx")
async def get_pgx(gene: str, drug: str):
    """Return PGx recommendation for a gene-drug pair from PharmGKB."""
    try:
        data = await get_pgx_recommendation(gene, drug)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"PGx lookup error: {str(e)}")

@router.post("/ddi")
async def check_ddi(payload: DDIRequest):
    """Check drug-drug interaction between two drugs."""
    try:
        data = await check_drug_interaction(payload.drug_a, payload.drug_b)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"DDI check error: {str(e)}")

@router.get("/faers/{drug_name}")
async def get_faers_events(drug_name: str, limit: int = 10):
    """Fetch adverse event reports for a drug from FDA openFDA."""
    try:
        data = await get_adverse_events(drug_name, limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FAERS API error: {str(e)}")
