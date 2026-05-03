from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
import logging

from src.api.classification_schemas import (
    ClassificationRequest,
    ClassificationResponse,
    ModelInfoResponse,
    BatchClassificationRequest,
    BatchClassificationResponse
)
from src.ml.classifier import PathogenicityClassifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/classification", tags=["classification"])

# Global classifier instance
_classifier = None


def get_classifier() -> PathogenicityClassifier:
    """Get or initialize global classifier"""
    global _classifier
    if _classifier is None:
        _classifier = PathogenicityClassifier()
    return _classifier


@router.post("/classify", response_model=ClassificationResponse)
async def classify_variant(
    request: ClassificationRequest,
    model_version: Optional[str] = Query(None, description="Model version (v1, v2, v3)")
) -> ClassificationResponse:
    """
    Classify variant pathogenicity.
    
    Accepts variant features and returns classification (Pathogenic/Benign/VUS)
    with confidence score and SHAP-based feature importance.
    """
    try:
        classifier = get_classifier()
        
        # Convert request to feature dictionary
        features = {
            'chrom': request.chrom,
            'pos': request.pos,
            'ref': request.ref,
            'alt': request.alt,
            'phyloP_score': request.phyloP_score,
            'SIFT_score': request.SIFT_score,
            'PolyPhen_score': request.PolyPhen_score,
            'CADD_score': request.CADD_score,
            'gnomAD_freq': request.gnomAD_freq,
            'REVEL_score': request.REVEL_score,
            'MutationTaster_score': request.MutationTaster_score,
            'FathmM_score': request.FathmM_score,
            'variant_type': request.variant_type,
            'amino_acid_change': request.amino_acid_change,
            'gene_symbol': request.gene_symbol
        }
        
        # Classify
        result = classifier.classify(features, version=model_version, include_interpretation=True)
        
        # Convert to response model
        response = ClassificationResponse(
            variant_id=f"{request.chrom}-{request.pos}-{request.ref}-{request.alt}",
            chrom=request.chrom,
            pos=request.pos,
            ref=request.ref,
            alt=request.alt,
            classification=result['classification'],
            confidence=result['confidence'],
            probabilities=result['probabilities'],
            model_version=result['model_version'],
            feature_importance=result.get('interpretation', {}).get('shap_values', {}),
            shape_values=result.get('interpretation', {}),
            clinical_significance=_get_clinical_significance(result['classification'])
        )
        
        logger.info(f"Classified variant: {response.variant_id} -> {response.classification}")
        return response
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Classification error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch_classify", response_model=BatchClassificationResponse)
async def batch_classify_variants(
    request: BatchClassificationRequest,
    model_version: Optional[str] = Query(None)
) -> BatchClassificationResponse:
    """
    Classify multiple variants in batch.
    
    Returns classifications for all variants.
    """
    try:
        classifier = get_classifier()
        
        # Convert requests to features
        variants_list = []
        for var_req in request.variants:
            features = {
                'chrom': var_req.chrom,
                'pos': var_req.pos,
                'ref': var_req.ref,
                'alt': var_req.alt,
                'phyloP_score': var_req.phyloP_score,
                'SIFT_score': var_req.SIFT_score,
                'PolyPhen_score': var_req.PolyPhen_score,
                'CADD_score': var_req.CADD_score,
                'gnomAD_freq': var_req.gnomAD_freq,
                'REVEL_score': var_req.REVEL_score,
                'MutationTaster_score': var_req.MutationTaster_score,
                'FathmM_score': var_req.FathmM_score,
                'variant_type': var_req.variant_type,
                'amino_acid_change': var_req.amino_acid_change,
                'gene_symbol': var_req.gene_symbol
            }
            variants_list.append(features)
        
        # Batch classify
        results = classifier.batch_classify(variants_list, version=model_version)
        
        # Convert to response format
        classifications = []
        for i, result in enumerate(results):
            if 'error' not in result:
                classifications.append({
                    'variant_id': f"{result['variant']['chrom']}-{result['variant']['pos']}-{result['variant']['ref']}-{result['variant']['alt']}",
                    'classification': result['classification'],
                    'confidence': result['confidence'],
                    'probabilities': result['probabilities']
                })
            else:
                classifications.append({
                    'variant_id': str(i),
                    'error': result['error'],
                    'classification': 'ERROR'
                })
        
        logger.info(f"Batch classified {len(classifications)} variants")
        
        return BatchClassificationResponse(
            total_variants=len(request.variants),
            classifications=classifications,
            model_version=model_version or 'v2'
        )
    
    except Exception as e:
        logger.error(f"Batch classification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model_info", response_model=ModelInfoResponse)
async def get_model_info(
    model_version: Optional[str] = Query(None, description="Model version")
) -> ModelInfoResponse:
    """
    Get model metadata and information.
    
    Returns model version, performance metrics, features, and training date.
    """
    try:
        classifier = get_classifier()
        model_info = classifier.get_model_info(model_version)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        response = ModelInfoResponse(
            model_name=model_info.get('name'),
            version=model_info.get('version'),
            model_type=model_info.get('model_type'),
            description=model_info.get('description'),
            features=model_info.get('features'),
            performance=model_info.get('performance'),
            registered_at=model_info.get('registered_at')
        )
        
        logger.info(f"Retrieved model info for {model_info.get('name')}:{model_info.get('version')}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model_versions")
async def list_model_versions() -> Dict[str, Any]:
    """
    List all available model versions.
    """
    try:
        classifier = get_classifier()
        models = classifier.list_available_models()
        
        versions = [
            {
                'version': m.get('version'),
                'description': m.get('description'),
                'registered_at': m.get('registered_at')
            }
            for m in models
        ]
        
        return {
            'model_name': classifier.model_name,
            'versions': versions,
            'total_versions': len(versions)
        }
    
    except Exception as e:
        logger.error(f"Error listing model versions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shap_values/{variant_id}")
async def get_shap_values(
    variant_id: str,
    model_version: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Get detailed SHAP-based feature importance for a variant.
    
    Returns SHAP values, base values, and feature contributions for interpretation.
    """
    try:
        # Parse variant ID (chrom-pos-ref-alt)
        parts = variant_id.split('-')
        if len(parts) < 4:
            raise HTTPException(
                status_code=400,
                detail="Invalid variant ID format. Expected: chrom-pos-ref-alt"
            )
        
        # Mock features for demonstration
        features = {
            'chrom': parts[0],
            'pos': int(parts[1]),
            'ref': parts[2],
            'alt': parts[3],
            'phyloP_score': 2.5,
            'SIFT_score': 0.1,
            'PolyPhen_score': 0.8,
            'CADD_score': 25.0,
            'gnomAD_freq': 0.0001,
            'REVEL_score': 0.7,
            'MutationTaster_score': 0.9,
            'FathmM_score': -1.5,
            'variant_type': 'SNP',
            'amino_acid_change': 'D123H'
        }
        
        classifier = get_classifier()
        result = classifier.classify(features, version=model_version, include_interpretation=True)
        
        return {
            'variant_id': variant_id,
            'model_version': result['model_version'],
            'interpretation': result.get('interpretation', {}),
            'classification': result['classification']
        }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid variant ID format")
    except Exception as e:
        logger.error(f"Error getting SHAP values: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_clinical_significance(classification: str) -> str:
    """Map classification to clinical significance"""
    mapping = {
        'Pathogenic': 'Pathogenic',
        'Benign': 'Benign',
        'VUS': 'Uncertain'
    }
    return mapping.get(classification, 'Unknown')
