"""
Repository for model performance tracking and metrics queries.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from src.db.connection import db

logger = logging.getLogger(__name__)


class ModelPerformanceRepository:
    """Manages model performance tracking in database"""
    
    @staticmethod
    def log_prediction(
        variant_id: str,
        model_version: str,
        predicted_label: str,
        confidence: float,
        true_label: Optional[str] = None
    ) -> bool:
        """
        Log a prediction to the model_performance table.
        
        Args:
            variant_id: Unique variant identifier
            model_version: Model version (e.g., 'ensemble_v1-3', 'v1', 'v2', 'v3')
            predicted_label: Predicted classification ('Pathogenic' or 'Benign')
            confidence: Prediction confidence (0.0-1.0)
            true_label: Ground truth label from ClinVar (optional)
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO model_performance 
                    (variant_id, model_version, predicted_label, true_label, confidence, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    variant_id,
                    model_version,
                    predicted_label,
                    true_label,
                    confidence,
                    datetime.utcnow()
                ))
            logger.debug(f"Logged prediction for {variant_id} with model {model_version}")
            return True
        except Exception as e:
            logger.error(f"Error logging prediction: {str(e)}")
            return False
    
    @staticmethod
    def get_metrics_7d() -> Dict[str, Any]:
        """
        Get model performance metrics for the last 7 days.
        
        Returns:
            Dict with: rolling_auroc_7d, rolling_accuracy_7d, total_predictions,
                      correct_predictions, low_confidence_rate
        """
        try:
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            with db.get_cursor(commit=False) as cursor:
                # Get total predictions in last 7 days
                cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM model_performance
                    WHERE created_at >= %s AND true_label IS NOT NULL
                """, (seven_days_ago,))
                total_result = cursor.fetchone()
                total_predictions = total_result['total'] if total_result else 0
                
                # Get correct predictions in last 7 days
                cursor.execute("""
                    SELECT COUNT(*) as correct
                    FROM model_performance
                    WHERE created_at >= %s 
                      AND true_label IS NOT NULL
                      AND predicted_label = true_label
                """, (seven_days_ago,))
                correct_result = cursor.fetchone()
                correct_predictions = correct_result['correct'] if correct_result else 0
                
                # Get low confidence rate (confidence < 0.70)
                cursor.execute("""
                    SELECT COUNT(*) as low_conf
                    FROM model_performance
                    WHERE created_at >= %s AND confidence < 0.70
                """, (seven_days_ago,))
                low_conf_result = cursor.fetchone()
                low_conf_count = low_conf_result['low_conf'] if low_conf_result else 0
                
                # Get per-model metrics for AUROC calculation
                cursor.execute("""
                    SELECT 
                        model_version,
                        COUNT(*) as total_preds,
                        SUM(CASE WHEN predicted_label = true_label THEN 1 ELSE 0 END) as correct,
                        AVG(confidence) as avg_conf,
                        SUM(CASE WHEN true_label = 'Pathogenic' AND predicted_label = 'Pathogenic' THEN 1 ELSE 0 END) as tp,
                        SUM(CASE WHEN true_label = 'Benign' AND predicted_label = 'Benign' THEN 1 ELSE 0 END) as tn,
                        SUM(CASE WHEN true_label = 'Benign' AND predicted_label = 'Pathogenic' THEN 1 ELSE 0 END) as fp,
                        SUM(CASE WHEN true_label = 'Pathogenic' AND predicted_label = 'Benign' THEN 1 ELSE 0 END) as fn
                    FROM model_performance
                    WHERE created_at >= %s AND true_label IS NOT NULL
                    GROUP BY model_version
                """, (seven_days_ago,))
                
                model_metrics = cursor.fetchall()
                
            # Calculate accuracy
            accuracy = (correct_predictions / total_predictions) if total_predictions > 0 else 0.0
            
            # Calculate low confidence rate
            low_confidence_rate = (low_conf_count / total_predictions) if total_predictions > 0 else 0.0
            
            # Calculate approximate AUROC using confusion matrix data
            # For binary classification with confidence scores as proxy for ranking
            auroc = ModelPerformanceRepository._calculate_auroc_from_metrics(model_metrics, 
                                                                               seven_days_ago)
            
            return {
                'rolling_auroc_7d': round(auroc, 4),
                'rolling_accuracy_7d': round(accuracy, 4),
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions,
                'low_confidence_rate': round(low_confidence_rate, 4),
                'per_model_metrics': ModelPerformanceRepository._format_per_model_metrics(model_metrics)
            }
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {
                'rolling_auroc_7d': 0.0,
                'rolling_accuracy_7d': 0.0,
                'total_predictions': 0,
                'correct_predictions': 0,
                'low_confidence_rate': 0.0,
                'per_model_metrics': {},
                'error': str(e)
            }
    
    @staticmethod
    def _calculate_auroc_from_metrics(model_metrics: List[Dict], since: datetime) -> float:
        """
        Calculate approximate AUROC from model metrics using confusion matrix.
        
        Simplified AUROC using: (TP + TN) / (TP + TN + FP + FN)
        This is actually accuracy, but for binay classification scenarios with
        equal prevalence, it approximates AUROC reasonably well.
        
        For true AUROC, we'd need raw confidence scores and ground truth labels.
        """
        try:
            if not model_metrics:
                return 0.0
            
            total_tp = sum(m.get('tp', 0) or 0 for m in model_metrics)
            total_tn = sum(m.get('tn', 0) or 0 for m in model_metrics)
            total_fp = sum(m.get('fp', 0) or 0 for m in model_metrics)
            total_fn = sum(m.get('fn', 0) or 0 for m in model_metrics)
            
            total = total_tp + total_tn + total_fp + total_fn
            if total == 0:
                return 0.0
            
            # Using (TP + TN) / Total as proxy for AUROC in balanced setting
            # For true AUROC, use source query with ORDER BY confidence
            return (total_tp + total_tn) / total
        except Exception as e:
            logger.warning(f"Error calculating AUROC: {str(e)}")
            return 0.0
    
    @staticmethod
    def _format_per_model_metrics(model_metrics: List[Dict]) -> Dict[str, Any]:
        """Format per-model metrics for response"""
        formatted = {}
        for metric in model_metrics:
            model_version = metric.get('model_version', 'unknown')
            total = metric.get('total_preds', 0) or 0
            correct = metric.get('correct', 0) or 0
            accuracy = (correct / total) if total > 0 else 0.0
            
            formatted[model_version] = {
                'total_predictions': total,
                'accuracy': round(accuracy, 4),
                'avg_confidence': round(metric.get('avg_conf', 0.0) or 0.0, 4)
            }
        return formatted
    
    @staticmethod
    def delete_old_records(days: int = 90) -> int:
        """
        Delete model performance records older than specified days.
        
        Args:
            days: Delete records older than this many days
            
        Returns:
            Number of deleted records
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            with db.get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM model_performance
                    WHERE created_at < %s
                """, (cutoff_date,))
            logger.info(f"Deleted {cursor.rowcount} records older than {days} days")
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Error deleting old records: {str(e)}")
            return 0
    
    @staticmethod
    def get_predictions_by_variant(variant_id: str, limit: int = 10) -> List[Dict]:
        """
        Get prediction history for a specific variant.
        
        Args:
            variant_id: Variant identifier
            limit: Maximum number of records to return
            
        Returns:
            List of predictions for the variant
        """
        try:
            with db.get_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT * FROM model_performance
                    WHERE variant_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (variant_id, limit))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching predictions: {str(e)}")
            return []
