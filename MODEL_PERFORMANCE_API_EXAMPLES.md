# Model Performance Tracking - API Examples

## Testing the Endpoints

### 1. Get Model Metrics

```bash
# Basic query
curl -X GET "http://localhost:8000/api/v1/classification/models/metrics"

# With JSON pretty-print
curl -X GET "http://localhost:8000/api/v1/classification/models/metrics" | jq

# Expected response:
{
  "rolling_auroc_7d": 0.9234,
  "rolling_accuracy_7d": 0.8847,
  "total_predictions": 589,
  "correct_predictions": 521,
  "low_confidence_rate": 0.0782,
  "model_drift_alert": false,
  "per_model_metrics": {
    "ensemble_v1-3": {
      "total_predictions": 589,
      "accuracy": 0.8847,
      "avg_confidence": 0.8521
    },
    "v1": {
      "total_predictions": 156,
      "accuracy": 0.8718,
      "avg_confidence": 0.8234
    },
    "v2": {
      "total_predictions": 203,
      "accuracy": 0.8768,
      "avg_confidence": 0.8589
    },
    "v3": {
      "total_predictions": 230,
      "accuracy": 0.8956,
      "avg_confidence": 0.8734
    }
  }
}
```

### 2. Get Extended Health Status

```bash
# Check health with drift alert status
curl -X GET "http://localhost:8000/api/v1/classification/health/extended"

# Pretty-print
curl -X GET "http://localhost:8000/api/v1/classification/health/extended" | jq

# Expected response:
{
  "status": "healthy",
  "timestamp": "2026-05-03T10:45:30.123456",
  "model_drift_alert": false,
  "models_available": ["ensemble_v1-3", "v1", "v2", "v3"]
}
```

## Python Integration Examples

### Example 1: Log a Prediction

```python
import requests

# Classify a variant first
classify_request = {
    "chrom": "17",
    "pos": 7571720,
    "ref": "G",
    "alt": "A",
    "phyloP_score": 3.0,
    "SIFT_score": 0.01,
    "PolyPhen_score": 0.95,
    "CADD_score": 30.0,
    "gnomAD_freq": 0.00001,
    "REVEL_score": 0.85,
    "MutationTaster_score": 0.95,
    "FathmM_score": -2.5,
    "variant_type": "SNP",
    "amino_acid_change": "p.R175H",
    "gene_symbol": "TP53",
    "clinvar_classification": "Pathogenic"  # Ground truth
}

response = requests.post(
    "http://localhost:8000/api/v1/classification/classify",
    json=classify_request
)

result = response.json()
print(f"Classification: {result['classification']}")
print(f"Confidence: {result['confidence']}")

# Then log the prediction (if your endpoint is updated)
from src.api.variant_analysis import ModelPerformanceTracker

ModelPerformanceTracker.log_prediction_with_ground_truth(
    variant_id=result['variant_id'],
    model_version=result['model_version'],
    predicted_label=result['classification'],
    confidence=result['confidence'],
    variant_info={
        'gene_symbol': classify_request['gene_symbol'],
        'mutation_notation': classify_request['amino_acid_change']
    },
    clinvar_classification=classify_request['clinvar_classification']
)

print(f"Prediction logged for {result['variant_id']}")
```

### Example 2: Monitor Metrics Over Time

```python
import requests
import time
from datetime import datetime

def monitor_model_performance(interval_seconds=300):
    """Monitor model performance every N seconds"""
    url = "http://localhost:8000/api/v1/classification/models/metrics"
    
    print("Starting model performance monitoring...")
    
    while True:
        try:
            response = requests.get(url, timeout=10)
            metrics = response.json()
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] Model Performance Report")
            print("=" * 50)
            print(f"AUROC (7d):     {metrics['rolling_auroc_7d']:.4f}")
            print(f"Accuracy (7d):  {metrics['rolling_accuracy_7d']:.4f}")
            print(f"Total Preds:    {metrics['total_predictions']}")
            print(f"Correct:        {metrics['correct_predictions']}")
            print(f"Accuracy:       {metrics['correct_predictions']/metrics['total_predictions']:.2%}" 
                  if metrics['total_predictions'] > 0 else "N/A")
            print(f"Low Conf Rate:  {metrics['low_confidence_rate']:.2%}")
            print(f"Drift Alert:    {'⚠️  YES' if metrics['model_drift_alert'] else '✓ NO'}")
            
            # Per-model breakdown
            print("\nPer-Model Metrics:")
            for model, stats in metrics.get('per_model_metrics', {}).items():
                print(f"  {model:20} Accuracy: {stats['accuracy']:.4f}, "
                      f"Avg Conf: {stats['avg_confidence']:.4f}")
            
            # Alerts
            if metrics['model_drift_alert']:
                print("\n⚠️  ALERT: Model drift detected! AUROC < 0.80")
                # Send notification here
            
            if metrics['rolling_accuracy_7d'] < 0.75:
                print("\n⚠️  ALERT: Accuracy below 0.75!")
                # Send notification here
            
            if metrics['low_confidence_rate'] > 0.20:
                print(f"\n⚠️  ALERT: High low-confidence rate: {metrics['low_confidence_rate']:.1%}")
                # Send notification here
            
        except requests.exceptions.ConnectionError:
            print(f"[{datetime.now()}] ERROR: Could not connect to API")
        except Exception as e:
            print(f"[{datetime.now()}] ERROR: {str(e)}")
        
        time.sleep(interval_seconds)

# Run monitoring (check every 5 minutes)
if __name__ == "__main__":
    monitor_model_performance(interval_seconds=300)
```

### Example 3: Query Metrics Programmatically

```python
from src.db.model_performance_repository import ModelPerformanceRepository

def generate_performance_report():
    """Generate a performance report from metrics"""
    metrics = ModelPerformanceRepository.get_metrics_7d()
    
    report = f"""
    ╔════════════════════════════════════════════╗
    ║      MODEL PERFORMANCE REPORT (7-DAY)      ║
    ╚════════════════════════════════════════════╝
    
    Overall Metrics:
    ├─ AUROC:           {metrics['rolling_auroc_7d']:.4f}
    ├─ Accuracy:        {metrics['rolling_accuracy_7d']:.4f}
    ├─ Total Pred:      {metrics['total_predictions']}
    ├─ Correct:         {metrics['correct_predictions']}
    └─ Low Conf Rate:   {metrics['low_confidence_rate']:.2%}
    
    Per-Model Performance:
    """
    
    for model, stats in metrics.get('per_model_metrics', {}).items():
        report += f"\n  {model}:"
        report += f"\n    ├─ Accuracy:      {stats['accuracy']:.4f}"
        report += f"\n    └─ Avg Confidence: {stats['avg_confidence']:.4f}"
    
    report += f"\n\n    Status:  {'✓ HEALTHY' if metrics['rolling_auroc_7d'] >= 0.80 else '⚠️  DRIFT ALERT'}"
    
    return report

# Print the report
print(generate_performance_report())
```

### Example 4: Detect and Alert on Drift

```python
from src.db.model_performance_repository import ModelPerformanceRepository
from src.cache.redis_cache import RedisCache
import smtplib
from email.mime.text import MIMEText

def check_for_model_drift():
    """Check for model drift and send alerts"""
    
    metrics = ModelPerformanceRepository.get_metrics_7d()
    auroc = metrics['rolling_auroc_7d']
    accuracy = metrics['rolling_accuracy_7d']
    
    alerts = []
    
    # Check AUROC
    if auroc < 0.80:
        alerts.append(f"⚠️  DRIFT: AUROC={auroc:.4f} < 0.80")
    
    # Check accuracy
    if accuracy < 0.75:
        alerts.append(f"⚠️  CRITICAL: Accuracy={accuracy:.4f} < 0.75")
    
    # Check low confidence rate
    if metrics['low_confidence_rate'] > 0.20:
        alerts.append(f"⚠️  UNCERTAINTY: {metrics['low_confidence_rate']:.1%} low-confidence predictions")
    
    # Send alerts if any
    if alerts:
        for alert in alerts:
            print(alert)
            # send_email_alert(alert)  # Implement your alerting
            # send_slack_message(alert)  # Or your preferred method
            # send_pagerduty_incident(alert)
    
    # Check Redis alarm
    try:
        redis = RedisCache()
        drift_alarm = redis.get('model_drift_alert')
        if drift_alarm:
            print(f"Redis Alarm: {drift_alarm}")
    except Exception as e:
        print(f"Could not check Redis: {e}")
    
    return alerts

# Check for drift
check_for_model_drift()
```

### Example 5: Batch Test Data Entry

```python
from src.api.variant_analysis import ModelPerformanceTracker
from datetime import datetime

def load_test_predictions():
    """Load test prediction data for evaluation"""
    
    test_cases = [
        # Correct predictions
        {"var": "chr17_7571720_G_A", "model": "ensemble_v1-3", "pred": "Pathogenic", "truth": "Pathogenic", "conf": 0.92},
        {"var": "chr17_7571720_G_A", "model": "v1", "pred": "Pathogenic", "truth": "Pathogenic", "conf": 0.88},
        {"var": "chr17_7571720_G_A", "model": "v2", "pred": "Pathogenic", "truth": "Pathogenic", "conf": 0.90},
        {"var": "chr1_1000000_A_G", "model": "ensemble_v1-3", "pred": "Benign", "truth": "Benign", "conf": 0.95},
        {"var": "chr1_1000000_A_G", "model": "v3", "pred": "Benign", "truth": "Benign", "conf": 0.93},
        {"var": "chr22_12345_T_A", "model": "ensemble_v1-3", "pred": "Benign", "truth": "Benign", "conf": 0.87},
        {"var": "chr2_2000000_G_C", "model": "v2", "pred": "Pathogenic", "truth": "Pathogenic", "conf": 0.85},
        
        # Incorrect predictions
        {"var": "chr5_5000000_A_T", "model": "v1", "pred": "Benign", "truth": "Pathogenic", "conf": 0.62},
        {"var": "chr10_10000000_C_G", "model": "ensemble_v1-3", "pred": "Pathogenic", "truth": "Benign", "conf": 0.71},
        {"var": "chr13_13000000_T_G", "model": "v3", "pred": "Benign", "truth": "Pathogenic", "conf": 0.58},
    ]
    
    print(f"Loading {len(test_cases)} test predictions...")
    
    for i, tc in enumerate(test_cases, 1):
        ModelPerformanceTracker.log_prediction_with_ground_truth(
            variant_id=tc['var'],
            model_version=tc['model'],
            predicted_label=tc['pred'],
            confidence=tc['conf'],
            clinvar_classification=tc['truth']
        )
        print(f"  [{i}/{len(test_cases)}] {tc['var']} predicted {tc['pred']} (actual: {tc['truth']})")
    
    print(f"\nLoaded {len(test_cases)} test predictions")
    print("Expected accuracy: 7/10 = 0.70")

# Load test data
load_test_predictions()

# Check metrics
from src.db.model_performance_repository import ModelPerformanceRepository
metrics = ModelPerformanceRepository.get_metrics_7d()
print(f"\nActual accuracy: {metrics['rolling_accuracy_7d']:.2f}")
```

## Expected Output Examples

### Metrics with Healthy Model
```
{
  "rolling_auroc_7d": 0.9234,
  "rolling_accuracy_7d": 0.8847,
  "total_predictions": 589,
  "correct_predictions": 521,
  "low_confidence_rate": 0.0782,
  "model_drift_alert": false,
  "per_model_metrics": {
    "ensemble_v1-3": {
      "total_predictions": 589,
      "accuracy": 0.8847,
      "avg_confidence": 0.8521
    },
    ... (other models)
  }
}
```

### Metrics with Model Drift
```
{
  "rolling_auroc_7d": 0.7162,  ← Below 0.80
  "rolling_accuracy_7d": 0.7089,
  "total_predictions": 612,
  "correct_predictions": 434,
  "low_confidence_rate": 0.1534,
  "model_drift_alert": true,  ← Alert triggered
  "per_model_metrics": { ... }
}
```

## Response Status Codes

```
200 OK
  - Metrics retrieved successfully
  - Health status returned

500 Internal Server Error
  - Database connection failed
  - Query error
  - Redis connection failed
```

## Debugging Tips

### Check if Predictions are Being Logged

```bash
# Connect to database
psql -h localhost -U postgres -d theragenome

# Query predictions
SELECT COUNT(*) FROM model_performance;
SELECT * FROM model_performance LIMIT 5;
SELECT COUNT(*) FROM model_performance WHERE true_label IS NOT NULL;
```

### Check Redis Alert Status

```bash
# Connect to Redis
redis-cli

# Check drift alert
GET model_drift_alert
TTL model_drift_alert

# Manually set alert
SET model_drift_alert '{"alert": true, "auroc": 0.72}'
EXPIRE model_drift_alert 86400
```

### Test Individual Components

```python
# Test repository
from src.db.model_performance_repository import ModelPerformanceRepository
metrics = ModelPerformanceRepository.get_metrics_7d()
print(metrics)

# Test logging
from src.api.variant_analysis import ModelPerformanceTracker
success = ModelPerformanceTracker.log_prediction_with_ground_truth(
    variant_id='test_chr1_1000_A_G',
    model_version='v1',
    predicted_label='Pathogenic',
    confidence=0.85,
    clinvar_classification='Pathogenic'
)
print(f"Logged: {success}")

# Test Redis
from src.cache.redis_cache import RedisCache
redis = RedisCache()
redis.set('test_key', {'test': 'value'}, ttl_hours=1)
result = redis.get('test_key')
print(result)
```

---

For more details, see: `MODEL_PERFORMANCE_TRACKING.md` and `MODEL_PERFORMANCE_INTEGRATION_GUIDE.md`
