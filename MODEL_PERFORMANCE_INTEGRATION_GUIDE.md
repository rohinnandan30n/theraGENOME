# Model Performance Tracking Integration Guide

## Quick Start

This guide shows how to integrate the new model performance tracking into your existing variant classification workflow.

## Step 1: Enable Automatic Prediction Logging

Update the `/classify` endpoint in `src/api/classification.py` to automatically log predictions:

```python
# At the end of the classify_variant function, before returning response:

from src.api.variant_analysis import ModelPerformanceTracker

# Log the prediction
ModelPerformanceTracker.log_prediction_with_ground_truth(
    variant_id=response.variant_id,
    model_version=response.model_version,
    predicted_label=response.classification,
    confidence=response.confidence,
    variant_info={
        'gene_symbol': request.gene_symbol,
        'mutation_notation': request.amino_acid_change
    },
    clinvar_classification=request.clinvar_classification if hasattr(request, 'clinvar_classification') else None
)

logger.info(f"Logged prediction for {response.variant_id}")
return response
```

## Step 2: Update Request Schema (Optional)

If you want to accept ClinVar classification in the request:

```python
# In src/api/classification_schemas.py, update ClassificationRequest:

class ClassificationRequest(BaseModel):
    # ... existing fields ...
    clinvar_classification: Optional[str] = Field(
        None, 
        description="ClinVar classification for ground truth (Pathogenic, Likely pathogenic, Benign, Likely benign)"
    )
```

## Step 3: Query Metrics via API

Once predictions are being logged, query the metrics endpoint:

```bash
# Get 7-day model performance metrics
curl -X GET "http://localhost:8000/api/v1/classification/models/metrics"

# Response example:
{
  "rolling_auroc_7d": 0.9234,
  "rolling_accuracy_7d": 0.8847,
  "total_predictions": 589,
  "correct_predictions": 521,
  "low_confidence_rate": 0.0782,
  "model_drift_alert": false,
  "per_model_metrics": { ... }
}
```

## Step 4: Check Health with Drift Alert

Monitor model status in health checks:

```bash
# Get extended health status with drift alert
curl -X GET "http://localhost:8000/api/v1/classification/health/extended"

# Response example:
{
  "status": "healthy",
  "timestamp": "2026-05-03T10:45:30.123456",
  "model_drift_alert": false,
  "models_available": ["ensemble_v1-3", "v1", "v2", "v3"]
}
```

## Step 5: Setup Monitoring Dashboard

Create a simple monitoring script to track metrics:

```python
import requests
import time
from datetime import datetime

def monitor_model_performance(interval_seconds=300):
    """Monitor model performance every N seconds"""
    url = "http://localhost:8000/api/v1/classification/models/metrics"
    
    while True:
        try:
            response = requests.get(url)
            metrics = response.json()
            
            print(f"\n[{datetime.now().isoformat()}]")
            print(f"AUROC (7d):    {metrics['rolling_auroc_7d']:.4f}")
            print(f"Accuracy (7d): {metrics['rolling_accuracy_7d']:.4f}")
            print(f"Total Preds:   {metrics['total_predictions']}")
            print(f"Correct:       {metrics['correct_predictions']}")
            print(f"Low Conf Rate:  {metrics['low_confidence_rate']:.4f}")
            print(f"Drift Alert:   {metrics['model_drift_alert']}")
            
            # Alert if drift detected
            if metrics['model_drift_alert']:
                print("⚠️  MODEL DRIFT DETECTED - AUROC < 0.80")
                # Send notification (email, Slack, PagerDuty, etc.)
            
            # Alert if accuracy too low
            if metrics['rolling_accuracy_7d'] < 0.75:
                print("⚠️  CRITICAL - ACCURACY < 0.75")
                # Send notification
            
        except Exception as e:
            print(f"Error fetching metrics: {e}")
        
        time.sleep(interval_seconds)

if __name__ == "__main__":
    monitor_model_performance(interval_seconds=300)  # Check every 5 minutes
```

## Step 6: Schedule Cleanup Job

Setup a weekly cleanup to remove old records:

```python
# In a separate background task/scheduler file:

from APScheduler.schedulers.background import BackgroundScheduler
from src.db.model_performance_repository import ModelPerformanceRepository

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', day_of_week='sunday', hour=2, minute=0)
def cleanup_old_predictions():
    """Delete predictions older than 90 days every Sunday at 2 AM"""
    deleted_count = ModelPerformanceRepository.delete_old_records(days=90)
    print(f"Cleanup job: Deleted {deleted_count} records")

scheduler.start()
```

## Step 7: Setup Alerting Rules

Configure monitoring system to alert on these metrics:

```yaml
# Example Prometheus alerting rules
groups:
  - name: model_performance
    interval: 1m
    rules:
      - alert: ModelDriftDetected
        expr: model_drift_alert == 1
        for: 5m
        annotations:
          summary: "Model drift detected - AUROC < 0.80"
          
      - alert: LowModelAccuracy
        expr: rolling_accuracy_7d < 0.75
        for: 10m
        annotations:
          summary: "Model accuracy below 0.75"
          
      - alert: HighUncertaintyRate
        expr: low_confidence_rate > 0.20
        for: 10m
        annotations:
          summary: "High proportion of low-confidence predictions"
```

## Manual Testing

### Test Logging a Prediction

```python
from src.api.variant_analysis import ModelPerformanceTracker

# Log a test prediction
ModelPerformanceTracker.log_prediction_with_ground_truth(
    variant_id='test_chr17_7571720_G_A',
    model_version='ensemble_v1-3',
    predicted_label='Pathogenic',
    confidence=0.92,
    variant_info={'gene_symbol': 'TP53', 'mutation_notation': 'p.R175H'},
    clinvar_classification='Pathogenic'  # Correctly predicted
)

# Log an incorrect prediction
ModelPerformanceTracker.log_prediction_with_ground_truth(
    variant_id='test_chr1_1000000_A_G',
    model_version='v2',
    predicted_label='Pathogenic',
    confidence=0.65,
    clinvar_classification='Benign'  # Incorrectly predicted
)
```

### Test Metrics Query

```python
from src.db.model_performance_repository import ModelPerformanceRepository

metrics = ModelPerformanceRepository.get_metrics_7d()
print(f"Accuracy: {metrics['rolling_accuracy_7d']}")
print(f"AUROC: {metrics['rolling_auroc_7d']}")
print(f"Total: {metrics['total_predictions']}")
```

### Run Tests

```bash
# Run the model performance tracking tests
pytest tests/test_classification.py::TestModelPerformanceMetrics -v

# Run specific test
pytest tests/test_classification.py::TestModelPerformanceMetrics::test_model_performance_metrics_accuracy_calculation -v

# Run with coverage
pytest tests/test_classification.py::TestModelPerformanceMetrics --cov=src.db.model_performance_repository --cov=src.api.variant_analysis
```

## Expected Results After Integration

### Scenario 1: Healthy Model (Week 1)

```
AUROC (7d):    0.9234
Accuracy (7d): 0.8847
Total Preds:   589
Correct:       521
Low Conf Rate: 0.0782
Drift Alert:   false  ✓
Status:        OK
```

### Scenario 2: Model Drift (Week 2)

If model performance degrades:

```
AUROC (7d):    0.7265  ← Below 0.80 threshold
Accuracy (7d): 0.7198
Total Preds:   612
Correct:       440
Low Conf Rate: 0.1523  ← Increasing uncertainty
Drift Alert:   true  ⚠️
Status:        ALERT
```

**Actions to take:**
1. Review recent training data for anomalies
2. Check if input feature distributions changed
3. Evaluate candidate models for replacement
4. Investigate specific variants with wrong predictions
5. Retrain model with updated data

## Troubleshooting

### Issue: Metrics Endpoint Returns All Zeros

**Cause:** No predictions logged yet

**Solution:** 
1. Verify predictions are being logged: `SELECT * FROM model_performance LIMIT 5;`
2. Check logging code is called in classify endpoint
3. Verify ClinVar ground truth is provided for accuracy calculations

### Issue: AUROC Stuck at 0.0

**Cause:** Insufficient data for AUROC calculation (need ≥30 samples with ground truth)

**Solution:**
1. Accumulate more predictions with ground truth labels
2. Use simpler metrics first (accuracy, F1) while building data
3. Check SQL query: `SELECT COUNT(*) FROM model_performance WHERE true_label IS NOT NULL;`

### Issue: Drift Alert Not Clearing After Recovery

**Cause:** Redis TTL not expiring properly

**Solution:**
1. Verify Redis is running: `redis-cli ping`
2. Check TTL manually: `redis-cli ttl model_drift_alert`
3. Manually clear if stuck: `curl -X GET http://localhost:8000/api/v1/classification/models/metrics` (will clear if AUROC >= 0.80)

### Issue: Database Queries Slow

**Cause:** Table too large, missing indexes

**Solution:**
1. Verify indexes exist: `SELECT * FROM pg_indexes WHERE tablename='model_performance';`
2. Rebuild index if needed: `REINDEX TABLE model_performance;`
3. Archive old data: `DELETE FROM model_performance WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 year';`

## Advanced Customization

### Customize Drift Threshold

Edit `src/db/model_performance_repository.py` to change the AUROC threshold:

```python
# In get_metrics_7d():
auroc = metrics.get('rolling_auroc_7d', 0.0)
model_drift_alert = auroc < 0.75  # Change from 0.80 to your threshold
```

### Add Custom Metrics

Extend `ModelPerformanceRepository._calculate_auroc_from_metrics()` to calculate true AUROC from confidence scores:

```python
@staticmethod
def _calculate_true_auroc_from_confidence(y_true, y_conf):
    from sklearn.metrics import roc_auc_score
    # y_conf should be confidence scores for positive class
    return roc_auc_score(y_true_binary, y_conf)
```

### Store Additional Ground Truth

Extend `model_performance` table to include more details:

```sql
ALTER TABLE model_performance ADD COLUMN (
    clinvar_id VARCHAR(50),
    disease VARCHAR(255),
    prediction_time_ms INTEGER
);
```

## References

- Main implementation: [MODEL_PERFORMANCE_TRACKING.md](MODEL_PERFORMANCE_TRACKING.md)
- Code: [src/db/model_performance_repository.py](src/db/model_performance_repository.py)
- Tests: [tests/test_classification.py::TestModelPerformanceMetrics](tests/test_classification.py)
- API: [src/api/classification.py](src/api/classification.py)
