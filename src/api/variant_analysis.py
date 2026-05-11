"""
Post-classification validation for variant pathogenicity predictions.

Implements hotspot detection and validation against known ClinVar pathogenic variants.
Overrides low-confidence benign predictions for known pathogenic hotspots.
"""

from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class HotspotValidator:
    """Validates classifications against known pathogenic hotspots"""
    
    # Known pathogenic hotspots from ClinVar
    # Format: (gene_symbol, mutation_notation) -> (clinical_significance, gnomad_impact)
    PATHOGENIC_HOTSPOTS = {
        ('TP53', 'p.R175H'): {
            'clinvar_id': 'RCV000012312',
            'clinical_significance': 'Pathogenic',
            'gnomad_af': 0.00001,
            'disease': 'Li-Fraumeni syndrome',
            'mechanism': 'Loss of DNA binding domain'
        },
        ('TP53', 'R175H'): {
            'clinvar_id': 'RCV000012312',
            'clinical_significance': 'Pathogenic',
            'gnomad_af': 0.00001,
            'disease': 'Li-Fraumeni syndrome',
            'mechanism': 'Loss of DNA binding domain'
        },
        ('BRCA1', 'c.5266dupC'): {
            'clinvar_id': 'RCV000008886',
            'clinical_significance': 'Pathogenic',
            'gnomad_af': 0.00002,
            'disease': 'Breast and ovarian cancer',
            'mechanism': 'Frameshift - premature termination'
        },
        ('BRCA1', '5266dupC'): {
            'clinvar_id': 'RCV000008886',
            'clinical_significance': 'Pathogenic',
            'gnomad_af': 0.00002,
            'disease': 'Breast and ovarian cancer',
            'mechanism': 'Frameshift - premature termination'
        },
        ('KRAS', 'p.G12D'): {
            'clinvar_id': 'RCV000015420',
            'clinical_significance': 'Pathogenic',
            'gnomad_af': 0.00005,
            'disease': 'Somatic: Pancreatic adenocarcinoma',
            'mechanism': 'Constitutive GTPase activity - oncogenic'
        },
        ('KRAS', 'G12D'): {
            'clinvar_id': 'RCV000015420',
            'clinical_significance': 'Pathogenic',
            'gnomad_af': 0.00005,
            'disease': 'Somatic: Pancreatic adenocarcinoma',
            'mechanism': 'Constitutive GTPase activity - oncogenic'
        },
    }
    
    CONFIDENCE_THRESHOLD = 0.80
    
    @classmethod
    def validate_and_override(cls, 
                             result: Dict[str, Any],
                             gene_symbol: Optional[str] = None,
                             mutation_notation: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate classification result against hotspot database.
        
        If result is BENIGN for a known pathogenic hotspot with confidence < 0.80,
        override the classification and add flags.
        
        Args:
            result: Classification result dictionary
            gene_symbol: HGNC gene symbol
            mutation_notation: Mutation notation (protein or cDNA)
            
        Returns:
            Updated result dictionary with validation and flags
        """
        # Initialize flags and explanation
        if 'flags' not in result:
            result['flags'] = []
        if 'explanation' not in result:
            result['explanation'] = ''
        
        # Skip validation if no gene/mutation info provided
        if not gene_symbol or not mutation_notation:
            return result
        
        # Check if this is a known hotspot
        hotspot_key = (gene_symbol.upper(), mutation_notation)
        if hotspot_key not in cls.PATHOGENIC_HOTSPOTS:
            return result
        
        # Get hotspot info
        hotspot_info = cls.PATHOGENIC_HOTSPOTS[hotspot_key]
        
        # Check if we need to override: BENIGN prediction with low confidence
        if (result.get('classification') == 'Benign' and 
            result.get('confidence', 1.0) < cls.CONFIDENCE_THRESHOLD):
            
            logger.warning(
                f"Hotspot override triggered for {gene_symbol}:{mutation_notation}. "
                f"Model predicted BENIGN with confidence {result['confidence']:.2f}, "
                f"but this is a known pathogenic hotspot from ClinVar ({hotspot_info['clinvar_id']})."
            )
            
            # Override classification
            result['classification'] = 'Pathogenic'
            result['confidence'] = min(0.95, result['confidence'] + 0.15)  # Boost confidence
            
            # Add flags
            result['flags'].append('hotspot_override')
            result['flags'].append('review_required')
            
            # Update explanation
            override_reason = (
                f"Known ClinVar pathogenic hotspot overrides low-confidence benign prediction. "
                f"ClinVar ID: {hotspot_info['clinvar_id']}. "
                f"Disease: {hotspot_info['disease']}. "
                f"Mechanism: {hotspot_info['mechanism']}"
            )
            
            if result['explanation']:
                result['explanation'] += f" | {override_reason}"
            else:
                result['explanation'] = override_reason
            
            logger.info(f"Classification overridden to Pathogenic for {gene_symbol}:{mutation_notation}")
        
        # Check if this is a known hotspot but predicted BENIGN (even with high confidence)
        # Add informational flag
        if result.get('classification') != 'Pathogenic':
            result['flags'].append('hotspot_detected')
            if 'explanation' not in result or not result['explanation']:
                result['explanation'] = (
                    f"Hotspot detected: {gene_symbol}:{mutation_notation} "
                    f"(ClinVar: {hotspot_info['clinical_significance']})"
                )
        
        return result
    
    @classmethod
    def get_hotspot_info(cls, gene_symbol: str, mutation_notation: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a known hotspot.
        
        Args:
            gene_symbol: HGNC gene symbol
            mutation_notation: Mutation notation
            
        Returns:
            Hotspot information dictionary or None if not found
        """
        key = (gene_symbol.upper(), mutation_notation)
        return cls.PATHOGENIC_HOTSPOTS.get(key)
    
    @classmethod
    def list_hotspots(cls) -> List[Tuple[str, str]]:
        """
        List all known hotspot variants.
        
        Returns:
            List of (gene_symbol, mutation_notation) tuples
        """
        return list(cls.PATHOGENIC_HOTSPOTS.keys())


class ModelPerformanceTracker:
    """Tracks model predictions against ground truth from ClinVar"""
    
    # ClinVar classifications and their mapping
    CLINVAR_TO_LABEL_MAPPING = {
        'Pathogenic': 'Pathogenic',
        'Likely pathogenic': 'Pathogenic',
        'Benign': 'Benign',
        'Likely benign': 'Benign',
    }
    
    @classmethod
    def log_prediction_with_ground_truth(
        cls,
        variant_id: str,
        model_version: str,
        predicted_label: str,
        confidence: float,
        variant_info: Optional[Dict[str, Any]] = None,
        clinvar_classification: Optional[str] = None
    ) -> bool:
        """
        Log a model prediction to the database.
        
        Attempts to determine ground truth from provided ClinVar classification
        or from the hotspot database.
        
        Args:
            variant_id: Unique variant identifier
            model_version: Model version string
            predicted_label: Predicted classification ('Pathogenic' or 'Benign')
            confidence: Prediction confidence (0.0-1.0)
            variant_info: Optional dict with gene_symbol, mutation_notation, etc.
            clinvar_classification: Optional ClinVar classification for ground truth
            
        Returns:
            True if logged successfully
        """
        from src.db.model_performance_repository import ModelPerformanceRepository
        
        true_label = None
        
        # Try to get ground truth from provided ClinVar classification
        if clinvar_classification:
            true_label = cls.CLINVAR_TO_LABEL_MAPPING.get(clinvar_classification)
        
        # Try to get ground truth from hotspot database
        if not true_label and variant_info:
            gene_symbol = variant_info.get('gene_symbol')
            mutation_notation = variant_info.get('mutation_notation')
            
            if gene_symbol and mutation_notation:
                hotspot_info = HotspotValidator.get_hotspot_info(gene_symbol, mutation_notation)
                if hotspot_info:
                    clin_sig = hotspot_info.get('clinical_significance')
                    true_label = cls.CLINVAR_TO_LABEL_MAPPING.get(clin_sig)
        
        # Log the prediction
        success = ModelPerformanceRepository.log_prediction(
            variant_id=variant_id,
            model_version=model_version,
            predicted_label=predicted_label,
            confidence=confidence,
            true_label=true_label
        )
        
        if success and true_label:
            # Check if prediction was correct
            is_correct = (predicted_label == true_label)
            log_level = logging.INFO if is_correct else logging.WARNING
            logger.log(
                log_level,
                f"Model {model_version} prediction logged for {variant_id}: "
                f"predicted={predicted_label}, ground_truth={true_label}, "
                f"confidence={confidence:.3f}, correct={is_correct}"
            )
        
        return success
