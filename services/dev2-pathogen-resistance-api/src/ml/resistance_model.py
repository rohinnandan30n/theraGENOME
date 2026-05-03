"""Antibiotic resistance prediction module."""

from pathlib import Path
from typing import List, Dict, Any

from src.ml.model_loader import load_resistance_model


def predict_resistance(assembly_path: str) -> List[Dict[str, Any]]:
    """
    Predict antibiotic resistance profile from assembled genome.
    
    Currently uses dummy/mock predictions for demonstration.
    In production, this would integrate real ML models or resistance databases
    like CARD (Comprehensive Antibiotic Resistance Database).
    
    Args:
        assembly_path: Path to SPAdes assembly output directory
        
    Returns:
        List of resistance predictions with antibiotic name, resistance status, and confidence
    """
    assembly_dir = Path(assembly_path)
    
    # Validate assembly directory exists
    if not assembly_dir.exists():
        raise ValueError(f"Assembly directory not found: {assembly_path}")
    
    # Check for expected SPAdes output files
    expected_files = ["contigs.fasta", "scaffolds.fasta"]
    has_output = any((assembly_dir / f).exists() for f in expected_files)
    
    if not has_output:
        print("Assembly files not found - using mock data for prediction")
    
    # Mock resistance prediction based on assembly characteristics
    # In production, this would:
    # 1. Extract sequences from contigs/scaffolds
    # 2. Query against CARD or similar database
    # 3. Identify resistance genes
    # 4. Calculate confidence scores from alignment quality
    
    resistance_profile = [
        {
            "antibiotic": "ciprofloxacin",
            "resistant": True,
            "confidence": 0.87,
            "gene": "gyrA_mutation"
        },
        {
            "antibiotic": "ampicillin",
            "resistant": False,
            "confidence": 0.65,
            "gene": "bla_absent"
        },
        {
            "antibiotic": "tetracycline",
            "resistant": True,
            "confidence": 0.92,
            "gene": "tetR_efflux_pump"
        },
        {
            "antibiotic": "gentamicin",
            "resistant": False,
            "confidence": 0.78,
            "gene": "aac_absent"
        },
        {
            "antibiotic": "vancomycin",
            "resistant": False,
            "confidence": 0.95,
            "gene": "van_operon_absent"
        },
    ]
    
    return resistance_profile


def get_amr_features(sample_id: str) -> Dict[str, float]:
    """
    Extract antibiotic resistance (AMR) gene profile for a sample.
    
    In production, this would:
    1. Query genome database (NCBI, CARD, ResFinder)
    2. Identify resistance genes via sequence alignment
    3. Return normalized feature vectors

    Currently returns mock features based on sample_id hash for determinism.
    
    Args:
        sample_id: Identifier for the sample
        
    Returns:
        Dictionary mapping gene names to presence (0 or 1)
    """
    # Generate deterministic features based on sample_id for reproducibility
    sample_hash = hash(sample_id) % 100
    
    return {
        "gyrA_mutation": 1 if sample_hash % 3 == 0 else 0,
        "bla_gene": 1 if sample_hash % 5 == 0 else 0,
        "tetR": 1 if sample_hash % 7 == 0 else 0,
        "aac_gene": 1 if sample_hash % 11 == 0 else 0,
        "van_operon": 1 if sample_hash % 13 == 0 else 0,
    }


def predict_with_model(
    sample_id: str, 
    antibiotics: List[str]
) -> Dict[str, Any]:
    """
    Predict antibiotic resistance using trained ML model.
    
    Loads model, extracts AMR features, generates predictions with SHAP
    explainability values and alternative recommendations.
    
    Args:
        sample_id: Sample identifier for feature extraction
        antibiotics: List of antibiotics to predict for
        
    Returns:
        Dictionary with predictions, SHAP values, and alternative recommendations
    """
    # Load model
    model = load_resistance_model()
    
    # Extract features
    features = get_amr_features(sample_id)
    
    # Define antibiotic-to-gene mappings for interpretation
    antibiotic_gene_map = {
        "ciprofloxacin": ["gyrA_mutation"],
        "ampicillin": ["bla_gene"],
        "tetracycline": ["tetR"],
        "gentamicin": ["aac_gene"],
        "vancomycin": ["van_operon"],
        "meropenem": ["bla_gene", "aac_gene"],
        "colistin": ["gyrA_mutation"],
        "amikacin": ["aac_gene"],
    }
    
    # Generate predictions
    predictions = []
    resistant_antibiotics = set()
    
    for antibiotic in antibiotics:
        # Get prediction probability
        prob = model.predict(features)
        
        # Determine resistance category
        if prob >= 0.7:
            result = "Resistant"
            resistant_antibiotics.add(antibiotic)
            confidence = prob
        elif prob >= 0.4:
            result = "Intermediate"
            confidence = prob
        else:
            result = "Susceptible"
            confidence = 1.0 - prob
        
        # Get SHAP values for relevant genes
        all_shap = model.get_shap_values(features, prob)
        relevant_genes = antibiotic_gene_map.get(antibiotic, [])
        shap_values = {
            gene: all_shap.get(gene, 0.0) for gene in relevant_genes
        }
        
        predictions.append({
            "antibiotic": antibiotic,
            "result": result,
            "confidence": round(confidence, 2),
            "shap_values": shap_values,
        })
    
    # Generate alternative recommendations for resistant antibiotics
    alternative_pool = ["meropenem", "colistin", "amikacin"]
    recommended_alternatives = []
    
    if resistant_antibiotics:
        for alternative in alternative_pool:
            # Simulate confidence in alternatives based on features
            alt_prob = model.predict(features)
            alt_prob = max(0.0, alt_prob - 0.15)  # Assume alternatives work better
            if alt_prob < 0.4:
                recommended_alternatives.append(alternative)
    
    return {
        "sample_id": sample_id,
        "predictions": predictions,
        "recommended_alternatives": recommended_alternatives,
    }

