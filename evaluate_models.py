"""
Model evaluation script using ClinVar variant data.

Downloads ClinVar variant summary, constructs feature vectors, and evaluates
all three models individually and combined in an ensemble.

Outputs:
- Console: Performance metrics for each model and ensemble
- File: metrics_report.json with detailed results
- Assertion: Fails CI if any model AUROC < 0.75
"""

import gzip
import urllib.request
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClinVarDataLoader:
    """Loads and preprocesses ClinVar variant data"""
    
    CLINVAR_URL = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz"
    
    # ClinVar column indices (0-based)
    COLUMN_NAMES = [
        'AlleleID', 'Type', 'Name', 'GeneID', 'GeneSymbol', 'HGNC_ID', 'ClinicalSignificance',
        'ClinSigSimple', 'LastEvaluated', 'ReviewStatus', 'NumberSubmitters', 'Guidelines',
        'TestedInGTR', 'GTRLink', 'VariantID', 'dbSNPID', 'dbVARID', 'Phenotypes', 'PhenotypeIDs',
        'OriginSimple', 'Assembly', 'ChromosomeAccession', 'Chromosome', 'Start', 'Stop', 'ReferenceAllele',
        'AlternateAllele', 'Cytogenetic', 'ReviewStatusClinSigSimple', 'Notes', 'Display_GeneSymbol',
        'OMIMID', 'CCDSid', 'InterferingWithGenotype', 'PhenotypeDescription', 'DOMINANTorRECESSIVE',
        'NumberofIndividualsWithVariant', 'EthnicityDescription', 'MolecularConsequence', 'VariantID2',
        'AlleleFrequencyFormatted', 'AlleleFrequencySource', 'CADD', 'SIFT', 'PolyPhen', 'PhyloP', 'dbSNPAlleleFreq'
    ]
    
    VALID_SIGNIFICANCE = {
        'Pathogenic', 'Likely pathogenic', 'Benign', 'Likely benign'
    }
    
    def __init__(self, cache_dir: str = "./clinvar_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "variant_summary.txt"
    
    def download_clinvar(self, force: bool = False) -> Path:
        """
        Download ClinVar variant summary. Uses cache if available.
        
        Args:
            force: Force re-download even if cached
            
        Returns:
            Path to extracted file
        """
        if self.cache_file.exists() and not force:
            logger.info(f"Using cached ClinVar data: {self.cache_file}")
            return self.cache_file
        
        logger.info(f"Downloading ClinVar data from {self.CLINVAR_URL}")
        
        try:
            # Download gzip file to temp location
            gz_path = self.cache_dir / "variant_summary.txt.gz"
            
            logger.info("Fetching ClinVar data...")
            urllib.request.urlretrieve(self.CLINVAR_URL, gz_path)
            
            # Decompress
            logger.info(f"Decompressing ClinVar data...")
            with gzip.open(gz_path, 'rb') as f_in:
                with open(self.cache_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            gz_path.unlink()  # Remove gz file
            logger.info(f"ClinVar data saved to {self.cache_file}")
            
            return self.cache_file
            
        except Exception as e:
            logger.error(f"Failed to download ClinVar data: {str(e)}")
            raise
    
    def load_and_filter(self) -> pd.DataFrame:
        """
        Load ClinVar data and filter to valid variants.
        
        Returns:
            DataFrame with filtered variants
        """
        logger.info(f"Loading ClinVar data from {self.cache_file}")
        
        # Read with column names
        df = pd.read_csv(
            self.cache_file,
            sep='\t',
            comment='#',
            header=None,
            names=self.COLUMN_NAMES,
            dtype={
                'ClinicalSignificance': str,
                'ReviewStatus': str,
                'CADD': str,
                'SIFT': str,
                'PolyPhen': str,
                'PhyloP': str,
            },
            low_memory=False,
            on_bad_lines='skip'
        )
        
        logger.info(f"Total variants in ClinVar: {len(df)}")
        
        # Filter by clinical significance
        df = df[df['ClinicalSignificance'].isin(self.VALID_SIGNIFICANCE)]
        logger.info(f"After significance filter: {len(df)}")
        
        # Filter by review status (contains "criteria provided")
        df = df[df['ReviewStatus'].str.contains('criteria provided', case=False, na=False)]
        logger.info(f"After review status filter: {len(df)}")
        
        return df
    
    @staticmethod
    def parse_score(value: str, default: float = 0.5) -> float:
        """
        Parse score from ClinVar format.
        
        ClinVar sometimes stores multiple values (e.g., "0.5, 0.6")
        Take the first value if multiple.
        """
        if pd.isna(value) or value == '':
            return default
        
        try:
            # Handle multiple values
            if isinstance(value, str) and ',' in value:
                value = value.split(',')[0].strip()
            
            score = float(value)
            # Normalize to 0-1 range if needed
            if score > 1.0:
                score = score / 100.0
            return max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            return default


class FeatureExtractor:
    """Extracts features from ClinVar variants"""
    
    MUTATION_TYPE_MAPPING = {
        'single nucleotide variant': 0,
        'snv': 0,
        'deletion': 1,
        'insertion': 2,
        'indel': 3,
        'duplication': 4,
        'inversion': 5,
        'complex': 6,
        'unknown': 7,
    }
    
    @staticmethod
    def get_mutation_type(variant_type: str) -> float:
        """Convert variant type to numeric code"""
        if pd.isna(variant_type):
            return 7.0  # Unknown
        
        type_lower = str(variant_type).lower()
        return float(FeatureExtractor.MUTATION_TYPE_MAPPING.get(
            type_lower,
            7.0  # Default to Unknown
        ))
    
    @staticmethod
    def extract_features(row: pd.Series) -> Optional[Dict[str, float]]:
        """
        Extract features from ClinVar variant row.
        
        Returns:
            Feature dictionary or None if extraction fails
        """
        try:
            cadd_score = ClinVarDataLoader.parse_score(row.get('CADD'), default=20.0)
            sift_score = ClinVarDataLoader.parse_score(row.get('SIFT'), default=0.5)
            polyphen2_score = ClinVarDataLoader.parse_score(row.get('PolyPhen'), default=0.5)
            phylop_score = ClinVarDataLoader.parse_score(row.get('PhyloP'), default=0.0)
            
            # gnomAD allele frequency is harder to extract from ClinVar
            # Use AlleleFrequencyFormatted if available, otherwise 0
            gnomad_af = 0.0
            if pd.notna(row.get('AlleleFrequencyFormatted')):
                af_str = str(row['AlleleFrequencyFormatted'])
                try:
                    gnomad_af = float(af_str)
                except (ValueError, TypeError):
                    gnomad_af = 0.0
            
            mutation_type = FeatureExtractor.get_mutation_type(row.get('Type'))
            
            return {
                'cadd_score': float(cadd_score),
                'sift_score': float(sift_score),
                'polyphen2_score': float(polyphen2_score),
                'gnomad_af': float(gnomad_af),
                'phylop_score': float(phylop_score),
                'mutation_type': float(mutation_type),
            }
        except Exception as e:
            logger.warning(f"Failed to extract features for row: {str(e)}")
            return None
    
    @staticmethod
    def prepare_feature_vector(features: Dict[str, float]) -> np.ndarray:
        """Convert feature dict to model input vector"""
        return np.array([
            features['cadd_score'],
            features['sift_score'],
            features['polyphen2_score'],
            features['gnomad_af'],
            features['phylop_score'],
            features['mutation_type'],
        ], dtype=np.float32)


class ModelEvaluator:
    """Evaluates models on ClinVar test set"""
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models = {}
        self.models_loaded = {}
    
    def load_models(self):
        """Load all three model PKL files"""
        model_files = {
            'v1': 'pathogenicity_vv1.pkl',
            'v2': 'pathogenicity_vv2.pkl',
            'v3': 'pathogenicity_vv3.pkl',
        }
        
        for version, filename in model_files.items():
            model_path = self.models_dir / filename
            
            # Try alternate naming convention
            if not model_path.exists():
                alt_path = self.models_dir / f'pathogenicity_v{version}.pkl'
                if alt_path.exists():
                    model_path = alt_path
            
            try:
                if model_path.exists():
                    self.models[version] = joblib.load(model_path)
                    self.models_loaded[version] = True
                    logger.info(f"Loaded model {version} from {model_path}")
                else:
                    logger.warning(f"Model file not found: {model_path}")
                    self.models_loaded[version] = False
            except Exception as e:
                logger.error(f"Failed to load model {version}: {str(e)}")
                self.models_loaded[version] = False
    
    def get_predictions(self, X: np.ndarray, version: str = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get predictions for feature vectors.
        
        Returns:
            Tuple of (predictions, probabilities)
        """
        if version and version in self.models and self.models_loaded[version]:
            model = self.models[version]
            
            # Get predictions
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X.reshape(1, -1))[0]
                pred = 1 if proba[1] > 0.5 else 0
            else:
                pred = int(model.predict(X.reshape(1, -1))[0])
                proba = np.array([1 - pred, pred])
            
            return pred, proba[1]
        
        return None, None
    
    def evaluate(self, df: pd.DataFrame, features_list: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Evaluate all models on dataset.
        
        Args:
            df: DataFrame with ground truth
            features_list: List of feature dictionaries
            
        Returns:
            Dictionary with evaluation results
        """
        # Prepare ground truth labels
        y_true = []
        for _, row in df.iterrows():
            sig = row.get('ClinicalSignificance', '')
            # 1 = Pathogenic, 0 = Benign
            label = 1 if sig.lower().startswith('pathogenic') or sig.lower().startswith('likely pathogenic') else 0
            y_true.append(label)
        
        y_true = np.array(y_true)
        
        # Collect predictions from all models
        models_predictions = {}
        models_probabilities = {}
        
        for version in ['v1', 'v2', 'v3']:
            if not self.models_loaded.get(version):
                logger.warning(f"Skipping model {version} - not loaded")
                continue
            
            preds = []
            probs = []
            
            for features in features_list:
                if features is None:
                    # Use default prediction if feature extraction failed
                    preds.append(0)
                    probs.append(0.5)
                else:
                    X = FeatureExtractor.prepare_feature_vector(features)
                    pred, prob = self.get_predictions(X, version)
                    
                    if pred is not None:
                        preds.append(pred)
                        probs.append(prob)
                    else:
                        preds.append(0)
                        probs.append(0.5)
            
            models_predictions[version] = np.array(preds)
            models_probabilities[version] = np.array(probs)
        
        # Compute metrics for each model
        results = {
            'models': {},
            'ensemble': {},
            'test_set_size': len(y_true),
            'evaluated_at': datetime.utcnow().isoformat()
        }
        
        for version in ['v1', 'v2', 'v3']:
            if version not in models_predictions:
                continue
            
            y_pred = models_predictions[version]
            y_prob = models_probabilities[version]
            
            metrics = self._compute_metrics(y_true, y_pred, y_prob, f"Model {version}")
            results['models'][version] = metrics
        
        # Ensemble predictions (majority voting)
        ensemble_preds = []
        ensemble_probs = []
        
        for i in range(len(features_list)):
            votes = []
            probs_per_sample = []
            
            for version in ['v1', 'v2', 'v3']:
                if version in models_predictions:
                    votes.append(models_predictions[version][i])
                    probs_per_sample.append(models_probabilities[version][i])
            
            if votes:
                ensemble_pred = 1 if sum(votes) >= len(votes) / 2 else 0
                ensemble_prob = np.mean(probs_per_sample)
                ensemble_preds.append(ensemble_pred)
                ensemble_probs.append(ensemble_prob)
            else:
                ensemble_preds.append(0)
                ensemble_probs.append(0.5)
        
        ensemble_preds = np.array(ensemble_preds)
        ensemble_probs = np.array(ensemble_probs)
        
        ensemble_metrics = self._compute_metrics(y_true, ensemble_preds, ensemble_probs, "Ensemble")
        results['ensemble'] = ensemble_metrics
        
        return results
    
    @staticmethod
    def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray, 
                        model_name: str = "Model") -> Dict[str, Any]:
        """Compute evaluation metrics"""
        
        try:
            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            auroc = roc_auc_score(y_true, y_prob)
            cm = confusion_matrix(y_true, y_pred)
            
            logger.info(f"\n{model_name} Performance:")
            logger.info(f"  Accuracy:  {accuracy:.4f}")
            logger.info(f"  Precision: {precision:.4f}")
            logger.info(f"  Recall:    {recall:.4f}")
            logger.info(f"  F1 Score:  {f1:.4f}")
            logger.info(f"  AUROC:     {auroc:.4f}")
            logger.info(f"  Confusion Matrix:\n{cm}")
            
            return {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1),
                'auroc': float(auroc),
                'confusion_matrix': cm.tolist(),
                'classification_report': classification_report(y_true, y_pred, output_dict=True)
            }
        
        except Exception as e:
            logger.error(f"Error computing metrics: {str(e)}")
            return {
                'error': str(e),
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0,
                'auroc': 0.0,
                'confusion_matrix': []
            }
    
    @staticmethod
    def save_report(results: Dict[str, Any], output_file: str = "metrics_report.json"):
        """Save evaluation results to JSON file"""
        
        # Prepare report with required fields
        report = {
            'evaluated_at': results['evaluated_at'],
            'test_set_size': results['test_set_size'],
            'models': {},
            'ensemble': {}
        }
        
        # Add per-model metrics
        for version, metrics in results['models'].items():
            report['models'][version] = {
                'model_name': f'pathogenicity_{version}',
                'version': version,
                'auroc': metrics.get('auroc', 0.0),
                'precision': metrics.get('precision', 0.0),
                'recall': metrics.get('recall', 0.0),
                'f1': metrics.get('f1', 0.0),
                'accuracy': metrics.get('accuracy', 0.0),
                'confusion_matrix': metrics.get('confusion_matrix', [])
            }
        
        # Add ensemble metrics
        ensemble_metrics = results['ensemble']
        report['ensemble'] = {
            'model_name': 'ensemble_v1-3',
            'version': 'ensemble_v1-3',
            'auroc': ensemble_metrics.get('auroc', 0.0),
            'precision': ensemble_metrics.get('precision', 0.0),
            'recall': ensemble_metrics.get('recall', 0.0),
            'f1': ensemble_metrics.get('f1', 0.0),
            'accuracy': ensemble_metrics.get('accuracy', 0.0),
            'confusion_matrix': ensemble_metrics.get('confusion_matrix', [])
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Metrics report saved to {output_file}")
        
        return report


def validate_results(results: Dict[str, Any]):
    """
    Validate model performance.
    
    Raises:
        AssertionError if any model's AUROC < 0.75
    """
    
    logger.info("\n" + "="*60)
    logger.info("VALIDATION RESULTS")
    logger.info("="*60)
    
    all_aurocs = []
    
    # Check individual model AUROCs
    for version, metrics in results['models'].items():
        auroc = metrics.get('auroc', 0.0)
        all_aurocs.append((f"Model {version}", auroc))
        
        if auroc < 0.75:
            raise AssertionError(
                f"Model {version} AUROC ({auroc:.4f}) is below threshold (0.75). "
                f"This indicates model performance is insufficient. "
                f"Full metrics: {metrics}"
            )
    
    # Check ensemble AUROC
    ensemble_auroc = results['ensemble'].get('auroc', 0.0)
    all_aurocs.append(("Ensemble", ensemble_auroc))
    
    if ensemble_auroc < 0.75:
        raise AssertionError(
            f"Ensemble AUROC ({ensemble_auroc:.4f}) is below threshold (0.75). "
            f"Ensemble performance is insufficient. "
            f"Full metrics: {results['ensemble']}"
        )
    
    # Print summary
    logger.info("\nAUROC Summary:")
    for model_name, auroc in all_aurocs:
        status = "✓ PASS" if auroc >= 0.75 else "✗ FAIL"
        logger.info(f"  {model_name:20} AUROC: {auroc:.4f} {status}")
    
    logger.info("\n✓ All models meet AUROC threshold (0.75)")


def main():
    """Main evaluation script"""
    
    logger.info("Starting model evaluation against ClinVar data")
    
    try:
        # Load ClinVar data
        logger.info("\n" + "="*60)
        logger.info("LOADING CLINVAR DATA")
        logger.info("="*60)
        
        clinvar_loader = ClinVarDataLoader()
        clinvar_loader.download_clinvar()
        df = clinvar_loader.load_and_filter()
        
        logger.info(f"Loaded {len(df)} filtered ClinVar variants")
        
        # Extract features
        logger.info("\n" + "="*60)
        logger.info("EXTRACTING FEATURES")
        logger.info("="*60)
        
        features_list = []
        valid_count = 0
        
        for idx, (_, row) in enumerate(df.iterrows()):
            if idx % 1000 == 0:
                logger.info(f"  Processing variant {idx}/{len(df)}")
            
            features = FeatureExtractor.extract_features(row)
            if features is not None:
                valid_count += 1
            features_list.append(features)
        
        logger.info(f"Successfully extracted features for {valid_count}/{len(df)} variants")
        
        # Load models
        logger.info("\n" + "="*60)
        logger.info("LOADING MODELS")
        logger.info("="*60)
        
        evaluator = ModelEvaluator()
        evaluator.load_models()
        
        loaded_count = sum(1 for v in evaluator.models_loaded.values() if v)
        logger.info(f"Loaded {loaded_count}/3 models")
        
        if loaded_count == 0:
            raise RuntimeError("No models could be loaded!")
        
        # Evaluate models
        logger.info("\n" + "="*60)
        logger.info("EVALUATING MODELS")
        logger.info("="*60)
        
        results = evaluator.evaluate(df, features_list)
        
        # Save report
        logger.info("\n" + "="*60)
        logger.info("SAVING REPORT")
        logger.info("="*60)
        
        report = ModelEvaluator.save_report(results)
        
        # Validate results
        validate_results(results)
        
        logger.info("\n" + "="*60)
        logger.info("EVALUATION COMPLETE - ALL CHECKS PASSED ✓")
        logger.info("="*60)
        
        return 0
    
    except AssertionError as e:
        logger.error(f"\n✗ VALIDATION FAILED: {str(e)}")
        return 1
    
    except Exception as e:
        logger.error(f"\n✗ ERROR: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
