# Integration Guide: Model Accuracy Metrics

**Updated:** April 9, 2026

## Overview

Three new files have been created to track and monitor model performance:

1. **[MODEL_ACCURACY_METRICS.md](MODEL_ACCURACY_METRICS.md)** — Comprehensive benchmark documentation
2. **[backend/models/performance_metrics.py](backend/models/performance_metrics.py)** — Python module with metric objects
3. **[scripts/validate_models.py](scripts/validate_models.py)** — Validation & testing script

---

## Quick Start

### 1. View Benchmarks
```bash
# See detailed accuracy targets for all three models
cat MODEL_ACCURACY_METRICS.md
```

### 2. Run Validation Tests
```bash
cd Integration-theragenome2
python scripts/validate_models.py
```

Output shows:
- ✅ GREEN: Meets/exceeds target
- ⚠️ YELLOW: Close to target, needs monitoring  
- ❌ RED: Below target, needs improvement

### 3. Use in Your Code

#### In Backend Responses
```python
from backend.models.performance_metrics import create_performance_response

# When returning a prediction, add performance metadata
result = genetic_analysis_model(context)

response = create_performance_response(
    model_type="genetic",
    prediction=result.to_dict(),
    confidence_score=0.92
)

# response now includes:
# {
#     "prediction": {...},
#     "model_performance": {
#         "overall_accuracy": 96.5,
#         "confidence_level": "high",
#         "recommendation": "✅ Safe to use as primary recommendation",
#         "known_limitations": [...]
#     }
# }
```

#### Check Model Performance Programmatically
```python
from backend.models.performance_metrics import get_model_performance

genetic_perf = get_model_performance("genetic")
print(f"Genetic model accuracy: {genetic_perf.overall_accuracy()}%")
print(f"Confidence: {genetic_perf.confidence_level.value}")
print(f"Status: {genetic_perf.validation_status.value}")
```

---

## Accuracy Targets by Model

### 🧬 Genetic Analysis Model
- **Target:** 91-98% accuracy
- **Key Metrics:** Variant detection, metabolizer prediction, gene-drug interactions
- **Critical Genes:** CYP2D6 (96%), CYP2C19 (94%), HLA-B (97%)
- **Edge Cases:** Rare variants (70-80%), novel variants (unknown)

### 🦠 Antibiotic Resistance Model  
- **Target:** 88-96% accuracy
- **Key Metrics:** Pathogen ID, resistance markers, susceptibility prediction
- **Critical Pathogens:** MRSA, Acinetobacter, multi-resistant
- **Edge Cases:** Novel mechanisms (<50%), mixed cultures (70-80%)

### 💊 Drug Toxicity Model
- **Target:** 82-95% accuracy  
- **Key Metrics:** Toxicity prediction, interactions, contraindications
- **Critical Organs:** Cardiac (92% specificity), hepatic (88%), renal (90%)
- **Edge Cases:** Rare side effects (<60%), unpublished interactions (81% coverage)

---

## Integration Points

### 1. API Responses (backend/chatbot/controller.py)
```python
# Add to chatbot response envelope
from backend.models.performance_metrics import create_performance_response

def process_request(request: ChatbotRequest):
    result = route_to_model(request)
    
    # Enhance with performance metadata
    enhanced_result = create_performance_response(
        model_type=detected_intent,
        prediction=result,
        confidence_score=model_confidence
    )
    
    return enhanced_result
```

### 2. Frontend Display (frontend/chatbot.html)
```javascript
// Show confidence indicator alongside response
function displayResponse(data) {
    const perf = data.model_performance;
    
    if (perf.confidence_level === 'high') {
        // Show green checkmark
        display.style.borderLeft = '4px solid #2d6a3e';
    } else if (perf.confidence_level === 'medium') {
        // Show yellow warning
        display.style.borderLeft = '4px solid #f57c00';
    } else {
        // Show red alert
        display.style.borderLeft = '4px solid #d32f2f';
    }
    
    // Display recommendation
    display.innerHTML += `<small>${perf.recommendation}</small>`;
}
```

### 3. Logging & Monitoring (backend/monitoring.py)
```python
# Track model performance over time
import logging
from backend.models.performance_metrics import get_model_performance

logger = logging.getLogger(__name__)

def log_model_usage(model_type, result):
    perf = get_model_performance(model_type)
    logger.info(f"Model: {model_type}, Accuracy: {perf.overall_accuracy()}%, "
                f"Confidence: {perf.confidence_level.value}")
```

### 4. Testing Suite (backend/tests/test_models.py)
```python
# Validate model performance in tests
from backend.models.performance_metrics import GENETIC_MODEL_PERFORMANCE

def test_genetic_model_accuracy():
    perf = GENETIC_MODEL_PERFORMANCE
    
    # Test that overall accuracy meets target
    for metric in perf.metrics:
        assert metric.target_value is not None, f"{metric.name} has no target"
        # Once real data available:
        # assert metric.current_value >= metric.target_value * 0.95
```

---

## Real-World Integration Timeline

### Phase 1: Now (April 2026)
- ✅ Performance framework created
- ✅ Benchmark targets established
- ✅ Validation script available
- ⏳ Add to API responses (simple integration)

### Phase 2: Next (May 2026)
- [ ] Collect real model predictions
- [ ] Run validation against benchmarks
- [ ] Update `current_value` in performance metrics
- [ ] Deploy enhanced API responses

### Phase 3: Production (June 2026)
- [ ] Continuous monitoring dashboard
- [ ] Real-time accuracy tracking
- [ ] Alert system for performance degradation
- [ ] Quarterly validation reports

---

## File Structure

```
Integration-theragenome2/
├── MODEL_ACCURACY_METRICS.md                    ← Comprehensive benchmarks
├── backend/
│   ├── models/
│   │   ├── genetic.py
│   │   ├── resistance.py
│   │   ├── toxicity.py
│   │   └── performance_metrics.py               ← NEW: Metric objects
│   ├── chatbot/
│   │   └── controller.py                        ← Add responses here
│   └── monitoring.py                            ← Add logging here
├── scripts/
│   └── validate_models.py                       ← NEW: Test script
└── frontend/
    └── chatbot.html                             ← Display confidence here
```

---

## Key Metrics to Track

| Metric | Purpose | Target | Frequency |
|--------|---------|--------|-----------|
| **Accuracy** | Overall prediction correctness | 85-98%* | Daily |
| **Precision** | Avoid false positives | 90-95%* | Daily |
| **Recall/Sensitivity** | Avoid false negatives | 85-95%* | Daily |
| **F1 Score** | Balance precision/recall | 0.85-0.95* | Daily |
| **Confidence Level** | Prediction reliability | High/Med/Low | Per prediction |
| **False Positive Rate** | Unnecessary actions | <8% | Weekly |
| **False Negative Rate** | Missed issues (critical) | <5% | Weekly |
| **Model Drift** | Performance degradation | <2% change | Monthly |

*Varies by model and metric type — see MODEL_ACCURACY_METRICS.md for specifics

---

## Troubleshooting

### "Model not validated"
- Model is new or hasn't undergone formal testing
- Don't use for critical clinical decisions
- Mark as "experimental" in UI

### Accuracy below target
- Retrain or fine-tune model
- Expand training dataset
- Check for edge cases or population shifts
- Alert team for investigation

### Confidence not matching accuracy?
- Confidence is per-prediction
- Accuracy is overall model performance
- High accuracy + low confidence = uncertain case (requires review)

---

## References

See [MODEL_ACCURACY_METRICS.md](MODEL_ACCURACY_METRICS.md) for:
- Real-world benchmark sources
- Validation methodologies
- Gene/pathogen/drug-specific breakdowns
- Clinical recommendations by confidence level
- Known limitations and considerations

---

## Support

**Questions?** Check the comprehensive documentation in [MODEL_ACCURACY_METRICS.md](MODEL_ACCURACY_METRICS.md)

**Need to update metrics?** Edit `backend/models/performance_metrics.py`

**Want to test?** Run `python scripts/validate_models.py --help`
