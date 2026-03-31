"""
ML utilities for advanced model explanations and monitoring.
Includes SHAP integration (to be implemented) and model evaluation.
"""
import numpy as np
import logging
from typing import Dict, List, Tuple
from sklearn.metrics import confusion_matrix, roc_auc_score, roc_curve

logger = logging.getLogger(__name__)


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict:
    """
    Evaluate model performance on a test set.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_proba: Predicted probabilities
    
    Returns:
        Dictionary with evaluation metrics
    """
    try:
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

        # Sensitivity (recall)
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0

        # Specificity
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0

        # Precision
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0

        # F1 Score
        f1 = 2 * (precision * sensitivity) / (precision + sensitivity) if (precision + sensitivity) > 0 else 0

        # AUC-ROC
        auc_roc = roc_auc_score(y_true, y_proba)

        return {
            "sensitivity": round(sensitivity, 3),
            "specificity": round(specificity, 3),
            "precision": round(precision, 3),
            "f1_score": round(f1, 3),
            "auc_roc": round(auc_roc, 3),
            "confusion_matrix": {
                "true_negatives": int(tn),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_positives": int(tp),
            },
        }
    except Exception as e:
        logger.error(f"Error evaluating model: {e}")
        return {}


def get_roc_curve(y_true: np.ndarray, y_proba: np.ndarray) -> Dict:
    """
    Get ROC curve data for visualization.
    
    Returns:
        Dictionary with FPR, TPR, and thresholds
    """
    try:
        fpr, tpr, thresholds = roc_curve(y_true, y_proba)

        return {
            "false_positive_rate": fpr.tolist(),
            "true_positive_rate": tpr.tolist(),
            "thresholds": thresholds.tolist(),
        }
    except Exception as e:
        logger.error(f"Error calculating ROC curve: {e}")
        return {}


def get_feature_correlations(X: np.ndarray, feature_names: List[str]) -> Dict:
    """
    Calculate feature correlations for model interpretation.
    
    Args:
        X: Feature matrix (N x M)
        feature_names: List of feature names
    
    Returns:
        Correlation matrix and top correlations
    """
    try:
        correlation_matrix = np.corrcoef(X.T)

        # Find top correlations
        top_correlations = {}
        for i in range(len(feature_names)):
            for j in range(i + 1, len(feature_names)):
                corr = correlation_matrix[i, j]
                if abs(corr) > 0.5:  # Only high correlations
                    top_correlations[f"{feature_names[i]} - {feature_names[j]}"] = round(corr, 3)

        return {
            "correlation_matrix": correlation_matrix.tolist(),
            "top_correlations": top_correlations,
        }
    except Exception as e:
        logger.error(f"Error calculating correlations: {e}")
        return {}


def get_prediction_confidence_distribution(y_proba: np.ndarray) -> Dict:
    """
    Analyze distribution of prediction confidence.
    
    Args:
        y_proba: Predicted probabilities
    
    Returns:
        Statistics about confidence distribution
    """
    try:
        confidences = np.max(y_proba, axis=1)

        return {
            "mean_confidence": round(float(np.mean(confidences)), 3),
            "min_confidence": round(float(np.min(confidences)), 3),
            "max_confidence": round(float(np.max(confidences)), 3),
            "std_confidence": round(float(np.std(confidences)), 3),
            "high_confidence_ratio": round(float(np.sum(confidences > 0.9) / len(confidences)), 3),
            "low_confidence_ratio": round(float(np.sum(confidences < 0.6) / len(confidences)), 3),
        }
    except Exception as e:
        logger.error(f"Error analyzing confidence: {e}")
        return {}


# Future SHAP integration
def explain_prediction_shap(model, X: np.ndarray, feature_names: List[str]):
    """
    Generate SHAP explanations for predictions (future implementation).
    
    Requires: pip install shap
    
    Args:
        model: Trained model
        X: Feature matrix
        feature_names: List of feature names
    
    Returns:
        SHAP values for each prediction
    """
    try:
        import shap

        # Create explainer
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        return {
            "shap_values": shap_values,
            "base_value": explainer.expected_value,
            "feature_names": feature_names,
        }

    except ImportError:
        logger.warning("SHAP not installed. Install with: pip install shap")
        return None
    except Exception as e:
        logger.error(f"Error generating SHAP explanations: {e}")
        return None


def generate_model_report(model_info: Dict, eval_metrics: Dict) -> Dict:
    """
    Generate comprehensive model report.
    
    Args:
        model_info: Model information
        eval_metrics: Evaluation metrics
    
    Returns:
        Comprehensive report
    """
    return {
        "model_info": model_info,
        "evaluation_metrics": eval_metrics,
        "status": "production_ready" if eval_metrics.get("auc_roc", 0) > 0.7 else "needs_improvement",
    }
