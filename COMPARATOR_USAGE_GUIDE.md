# Treatment Comparator Usage Guide

## Quick Start

```python
from backend.chatbot.comparator import TreatmentComparator

# Initialize the comparator (stateless, can be reused)
comparator = TreatmentComparator()

# Compare multiple drugs
result = comparator.compare(
    drugs=["amoxicillin", "doxycycline"],
    context={}  # optional: shared genetic_data, infection_data, etc.
)
```

---

## Input Parameters

### `drugs` (required)
- **Type**: `list[str]`
- **Description**: List of drug names to compare
- **Requirement**: Minimum 2 drugs
- **Limit**: Maximum 4 drugs (enforced to prevent abuse)
- **Example**: `["amoxicillin", "doxycycline", "cephalexin"]`

### `context` (optional)
- **Type**: `dict[str, Any]`
- **Description**: Shared clinical context passed to each drug evaluation
- **Common fields**:
  - `genetic_data`: Patient's genetic profile (e.g., CYP2D6 variants)
  - `infection_data`: Infection/pathogen information
  - `patient_weight`: Patient weight for dose adjustments
  - Custom fields are preserved and passed through

**Example**:
```python
comparator.compare(
    drugs=["tramadol", "codeine"],
    context={
        "genetic_data": {
            "patient_metabolizer_status": "poor",
            "risk_alleles": ["CYP2D6*3", "CYP2D6*4"]
        }
    }
)
```

---

## Output Structure

### Success Response (template: `DRUG_COMPARISON`)

```json
{
  "intent": "compare_drugs",
  "template": "DRUG_COMPARISON",
  "variables": {
    "drugs": ["Drug A", "Drug B"]
  },
  "comparison": [
    {
      "drug": "Drug A",
      "result": {
        "risk_level": "low",        // "low" | "medium" | "high" | "unknown"
        "confidence": 0.85,          // 0.0 – 1.0
        "reason_codes": ["SAFE_METABOLIZATION", ...]
      }
    },
    {...}
  ],
  "ranking": [
    { "drug": "Drug A", "rank": 1 },
    { "drug": "Drug B", "rank": 2 }
  ],
  "summary": {
    "best_option": "Drug A",
    "decision_basis": [
      "LOWER_RISK",
      "HIGHER_CONFIDENCE"
    ]
  },
  "metadata": {
    "source": "comparator",
    "models_invoked": ["drug_toxicity_model", "genetic_analysis_model"],
    "errors": null
  }
}
```

### Insufficient Data Response (template: `INSUFFICIENT_DATA`)

```json
{
  "intent": "compare_drugs",
  "template": "INSUFFICIENT_DATA"
}
```

Returned when:
- Less than 2 drugs provided
- All drugs failed to evaluate
- Empty drug list

---

## Ranking Logic

### Scoring Algorithm

1. **Primary Score**: Based on `risk_level`
   | Level | Score |
   |-------|-------|
   | low | 3 |
   | medium | 2 |
   | high | 1 |
   | unknown | 0 |

2. **Tiebreaker Score**: Weighted combination
   - Base: Confidence score (0.0 – 1.0)
   - Effectiveness bonus: +30% if available
   - Toxicity penalty: -20% for high toxicity

3. **Final Rank**: Sorted descending (highest score = rank 1)

### Example

```
Drug A: risk_level="low" (3), confidence=0.80, effectiveness=90, toxicity=10
  → primary_score=3, tiebreaker=0.87
  → RANK 1

Drug B: risk_level="low" (3), confidence=0.75, effectiveness=70, toxicity=25
  → primary_score=3, tiebreaker=0.72
  → RANK 2

Drug C: risk_level="medium" (2), confidence=0.90
  → primary_score=2, tiebreaker=0.90
  → RANK 3 (lower primary score despite higher confidence)
```

---

## Decision Basis Codes

The `decision_basis` array contains machine-readable reasons why the best drug was selected. Possible values:

| Code | Meaning |
|------|---------|
| `LOWER_RISK` | Best option has lower clinical risk than alternatives |
| `LOWER_TOXICITY` | Best option has lower toxicity than alternatives |
| `HIGHER_EFFECTIVENESS` | Best option has better therapeutic effectiveness |
| `HIGHER_CONFIDENCE` | Best option has higher prediction confidence |

**Note**: Empty array `[]` means all drugs rank equally on these criteria, or the comparator hasn't identified clear differentiators.

---

## Use Cases

### 1. Patient-Specific Drug Selection

```python
comparator.compare(
    drugs=["metformin", "glyburide"],
    context={
        "genetic_data": {
            "risk_alleles": ["CYP3A5*3"],
            "metabolizer_status": "normal"
        },
        "patient_weight": 75  # kg
    }
)
```

### 2. Infection-Guided Antibiotic Choice

```python
comparator.compare(
    drugs=["amoxicillin", "ciprofloxacin", "azithromycin"],
    context={
        "infection_data": {
            "pathogen": "MRSA",
            "susceptibility": {
                "amoxicillin": "resistant",
                "ciprofloxacin": "susceptible",
                "azithromycin": "intermediate"
            }
        }
    }
)
```

### 3. Drug Holiday Safety Assessment

```python
comparator.compare(
    drugs=["warfarin_low_dose", "warfarin_standard", "apixaban"],
    context={
        "patient_age": 85,
        "renal_function": "mild_impairment",
        "genetic_data": {"VKORC1": "GG"}
    }
)
```

---

## Integration with Downstream Components

### Mode Filtering

The comparator output is passed to `ModeFilter` in the full pipeline:

```python
from backend.chatbot.controller import process_query

# Controller automatically applies mode filtering
response = process_query(
    user_input="Compare these drugs",
    mode="patient",  # or "doctor"
    context={"drugs": ["drugA", "drugB"]}
)
```

**Doctor mode** → Returns full model outputs  
**Patient mode** → Strips technical details

---

## Error Handling

### Invalid Input

```python
# Less than 2 drugs
result = comparator.compare(drugs=["single_drug"], context={})
# result["template"] == "INSUFFICIENT_DATA"

# Empty list
result = comparator.compare(drugs=[], context={})
# result["template"] == "INSUFFICIENT_DATA"
```

### Pipeline Failures

If individual drugs fail to evaluate, the comparator:
- Skips failed drugs
- Returns comparison only for successful ones
- Logs errors in metadata
- Still produces a ranked result if ≥2 drugs succeed

```python
result = comparator.compare(drugs=["valid_drug", "invalid_drug"], context={})
# Returns comparison with just "valid_drug" if "invalid_drug" fails
# result["metadata"]["errors"] = [{"drug": "invalid_drug", "error": "..."}]
```

---

## Performance Characteristics

- **Time Complexity**: O(n * m) where n = number of drugs, m = evaluation time per drug
- **Space Complexity**: O(n) for storing results
- **Throughput**: ~1-2 comparisons/second on typical hardware (depends on model inference time)
- **Caching**: None (stateless design)

---

## API Reference

### `TreatmentComparator`

```python
class TreatmentComparator:
    def compare(
        drugs: list[str],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]
```

**Parameters**:
- `drugs`: List of drug names (min 2, max 4)
- `context`: Optional shared clinical context

**Returns**: Comparison result dictionary

**Raises**: None (errors handled gracefully)

---

## Testing

Run the comparator tests:

```bash
# All comparator tests
pytest backend/tests/test_chatbot.py::TestTreatmentComparator -v

# Specific test
pytest backend/tests/test_chatbot.py::TestTreatmentComparator::test_ranking_consistency -v

# Full test suite
pytest backend/tests/ -v
```

---

## Best Practices

1. **Always provide context when available**
   - Better decisions with genetic/infection data
   - Empty context still works but may use defaults

2. **Compare 2-3 drugs**
   - 2-3 drugs: Optimal clarity
   - 4 drugs: Maximum allowed (good for multi-class options)
   - More than 4: Not supported (hits 4-drug cap)

3. **Use the ranking, not just the best option**
   - Full ranking provides clinical flexibility
   - Alternative options visible if best option has contraindications

4. **Check `decision_basis` codes**
   - Tells you WHY a drug was ranked best
   - Empty array suggests similar risk profiles

5. **Handle downstream mode filtering explicitly**
   - Comparator doesn't filter by mode
   - Use `process_query()` for automatic filtering
   - Use `ModeFilter` manually if needed

---

## Limitations

- ❌ Does NOT generate natural language explanations (use `ExplainerEngine`)
- ❌ Does NOT modify reason codes (pass-through from decision_engine)
- ❌ Does NOT filter by doctor/patient mode (handled downstream)
- ❌ Does NOT re-rank based on user preferences (stateless)
- ⚠️ Maximum 4 drugs per comparison (enforced)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `template: "INSUFFICIENT_DATA"` | Provide ≥2 drugs |
| Empty `decision_basis` | Drugs have similar risk profiles |
| All ranks the same | No clear differentiator found |
| Pipeline errors in metadata | Check context validity |
| Inconsistent ranking | Not possible (deterministic algorithm) |

---

## Contributing

When extending the comparator:

1. ✅ Keep reusing router + decision_engine
2. ✅ Maintain deterministic ranking
3. ✅ Don't filter by mode
4. ✅ Don't generate text
5. ✅ Add tests for new features
6. ✅ Update this guide

---

## Questions?

Refer to:
- [Implementation Details](./COMPARATOR_IMPLEMENTATION.md)
- [Test Suite](./backend/tests/test_chatbot.py) — See `TestTreatmentComparator` class
- Inline docstrings in [comparator.py](./backend/chatbot/comparator.py)
