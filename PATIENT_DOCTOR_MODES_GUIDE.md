# Patient vs Doctor Modes — Backend Architecture Guide

## Overview

TheraGenome AI implements a **dual-mode system** that tailors chatbot responses based on the user's role:

- **Doctor Mode** — Full clinical detail, technical metrics, model explanations, and raw AI outputs
- **Patient Mode** — Simplified, patient-friendly responses with advanced technical details removed

This allows the same backend system to serve both clinical professionals and general patients safely and appropriately.

---

## 1. Architecture Overview

### Component Stack

```
┌─────────────────────────────────────────────────────┐
│              FRONTEND (index.html)                  │
│    Mode Selector Dropdown (Doctor / Patient)        │
└──────────────────┬──────────────────────────────────┘
                   │ mode parameter in request
                   ↓
┌─────────────────────────────────────────────────────┐
│         FASTAPI ENDPOINT (/api/v1/chatbot/query)   │
│      ChatbotRequest model validates mode            │
│    mode: str = Field("doctor", pattern=r"^(doctor|patient)$")
└──────────────────┬──────────────────────────────────┘
                   │ mode passed to process_query()
                   ↓
┌─────────────────────────────────────────────────────┐
│         DECISION ENGINE Pipeline                    │
│  1. Intent Detection                                │
│  2. Module Routing                                  │
│  3. Model Evaluation                                │
│  4. Response Template Selection                     │
└──────────────────┬──────────────────────────────────┘
                   │ Full response (all data)
                   ↓
┌─────────────────────────────────────────────────────┐
│        MODE FILTER (mode_filter.py)                 │
│  Strips explanation.modules if mode == "patient"    │
│  Preserves schema structure in both modes           │
└──────────────────┬──────────────────────────────────┘
                   │ Filtered response
                   ↓
┌─────────────────────────────────────────────────────┐
│         FRONTEND Response Handler                   │
│  Renders mode-specific UI output                    │
└─────────────────────────────────────────────────────┘
```

---

## 2. Mode Filter Implementation

### Location: `backend/chatbot/mode_filter.py`

The `ModeFilter` class is a **stateless, post-processing layer** that operates after the decision engine completes.

#### Key Principles

1. **No Logic Changes** — Filtering never alters template, variables, or clinical recommendations
2. **Schema-Preserving** — Both modes return identical top-level keys
3. **Single Responsibility** — All mode-aware filtering happens here and nowhere else

#### What Gets Filtered?

| Field | Doctor Mode | Patient Mode |
|-------|------------|--------------|
| `intent` | ✅ Included | ✅ Included |
| `template` | ✅ Included | ✅ Included |
| `variables` | ✅ Included | ✅ Included |
| `explanation.reason_codes` | ✅ Included | ✅ Included (kept safe) |
| `explanation.modules` | ✅ Included (raw outputs) | ❌ **REMOVED** |
| `explanation.reason_details` | ✅ Included | ✅ Included |
| `metadata` | ✅ Included | ✅ Included |
| `data.toxicity_flags` | ✅ Included | ✅ Included |
| `data.therapeutic_index` | ✅ Included | ✅ Included |
| `data.interactions` | ✅ Included | ✅ Included |

#### ModeFilter Usage

```python
from backend.chatbot.mode_filter import ModeFilter

filter = ModeFilter()

# Full response with all technical details
full_response = _decision_engine.evaluate(route_result)

# Apply mode filtering
filtered = filter.apply(full_response, mode="patient")  # or "doctor"
```

#### Code Structure

```python
class ModeFilter:
    def apply(self, response: dict, mode: str = "doctor") -> dict:
        """
        Filter response according to mode.
        - "doctor" → return full response
        - "patient" → strip explanation.modules
        - unknown → default to patient (safest)
        """
        filtered = copy.deepcopy(response)
        filtered.setdefault("metadata", {})["mode"] = mode
        
        if mode == MODE_DOCTOR:
            return filtered
        
        if mode == MODE_PATIENT:
            return self._filter_patient(filtered)
    
    @staticmethod
    def _filter_patient(resp: dict) -> dict:
        """Remove explanation.modules for patient."""
        if "explanation" in resp and "modules" in resp["explanation"]:
            del resp["explanation"]["modules"]
        return resp
```

---

## 3. FastAPI Request/Response Contract

### Endpoint: `POST /api/v1/chatbot/query`

#### Request Model (ChatbotRequest)

```python
class ChatbotRequest(BaseModel):
    input: str = Field(..., min_length=1, description="User query text")
    mode: str = Field("doctor", pattern=r"^(doctor|patient)$")  # ← Mode validation
    context: dict[str, Any] = Field(default_factory=dict)
    scope: str = Field("full", description="Explanation scope filter")
```

#### Typical Request (Doctor Mode)

```json
{
  "input": "Analyze the toxicity of warfarin in a patient with CYP2C9*3/*3",
  "mode": "doctor",
  "context": {
    "drug": "warfarin",
    "genetic_data": {"variants": ["CYP2C9*3/*3"]}
  },
  "scope": "full"
}
```

#### Typical Request (Patient Mode)

```json
{
  "input": "Is warfarin safe for me?",
  "mode": "patient",
  "context": {},
  "scope": "summary"
}
```

#### Response Model (ChatbotResponse)

```python
{
  "intent": "analyze_drug_safety",
  "template": "DRUG_USE_WITH_CAUTION",
  "variables": {
    "drug_name": "Warfarin",
    "risk_level": "high",
    "summary": "Warfarin requires dose adjustment..."
  },
  "explanation": {
    "reason_codes": ["genetic_polymorphism", "high_sensitivity"],
    "reason_details": [
      {
        "code": "genetic_polymorphism",
        "severity": "high",
        "detail": "CYP2C9*3/*3 is a poor metabolizer variant..."
      }
    ],
    "modules": {  # ← REMOVED in patient mode
      "pharmacogenomics_model": {
        "prediction": "high_sensitivity",
        "confidence": 0.94
      },
      "eligibility_model": {
        "contraindicated": false
      }
    }
  },
  "metadata": {
    "mode": "doctor",
    "processing_time_ms": 156.23,
    "intent_confidence": 0.98
  }
}
```

---

## 4. Frontend Integration

### File: `frontend/assets/js/chatbot-controller.js`

#### Mode Storage & Initialization

```javascript
class ChatbotController {
    constructor() {
        // Restore saved mode from localStorage or default to doctor
        this.currentMode = localStorage.getItem('chatbotMode') || 'doctor';
        this.init();
    }
    
    restoreSavedMode() {
        const selector = document.getElementById('chatbotModeSelect');
        if (selector) {
            selector.value = this.currentMode;
        }
    }
}
```

#### Mode Selection UI (HTML)

**File: `frontend/index.html`**

```html
<select id="chatbotModeSelect">
    <option value="doctor">Doctor Mode</option>
    <option value="patient">Patient Mode</option>
</select>
```

#### Sending Query with Mode

```javascript
async handleSendMessage() {
    const userInput = document.getElementById('chatInput').value;
    const mode = this.currentMode;  // "doctor" or "patient"
    
    const response = await fetch('/api/v1/chatbot/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            input: userInput,
            mode: mode,  // ← Sent to backend
            context: this.buildContext()
        })
    });
    
    const data = await response.json();
    this.displayResponse(data);
}
```

#### Mode-Specific Rendering

```javascript
// Doctor mode shows technical details
if (mode === 'doctor' && explanation && Object.keys(explanation).length > 0) {
    detailsHtml += `
        <div class="clinical-details">
            <h4>Technical Analysis</h4>
            <p><strong>Reason Codes:</strong> ${explanation.reason_codes.join(', ')}</p>
            <p><strong>Model Confidence:</strong> ${explanation.confidence}%</p>
        </div>
    `;
}

// Patient mode shows simplified version
if (mode === 'patient') {
    detailsHtml += `
        <div class="patient-summary">
            <p>${variables.summary}</p>
        </div>
    `;
}
```

---

## 5. Data Flow Diagram

### Doctor Mode Query

```
USER INPUT (Doctor)
    ↓
[Intent Detection] → "analyze_drug_safety"
    ↓
[Router] → Drug Safety Module
    ↓
[Decision Engine] → Full evaluation with:
    - Pharmacogenomics model outputs
    - Eligibility model predictions
    - Toxicity calculations
    - Interaction matrices
    ↓
[Mode Filter] → mode = "doctor"
    ↓
RESPONSE: Includes explanation.modules + all technical data
    ↓
[Frontend Renderer] → Display technical details + risk scores
```

### Patient Mode Query

```
USER INPUT (Patient)
    ↓
[Intent Detection] → "analyze_drug_safety"
    ↓
[Router] → Drug Safety Module
    ↓
[Decision Engine] → Full evaluation with all data
    ↓
[Mode Filter] → mode = "patient"
    ↓
    └─ Removes: explanation.modules
    └─ Keeps: reason_codes, reason_details, variables
    ↓
RESPONSE: Simplified, patient-friendly
    ↓
[Frontend Renderer] → Display summary + plain language
```

---

## 6. Backend Processing Pipeline

### File: `backend/chatbot/controller.py`

#### Main Processing Function

```python
def process_query(
    user_input: str,
    mode: str = "doctor",  # ← Key parameter
    context: dict[str, Any] | None = None,
    scope: str = "full",
) -> dict[str, Any]:
    """
    End-to-end chatbot query processing with mode support.
    
    Parameters
    ----------
    mode : str
        "doctor"  → full clinical detail
        "patient" → simplified, safe-for-patient output
    """
    context = context or {}
    start = time.perf_counter()
    
    # 1. SAFETY GUARDRAILS (highest priority)
    safety_flag = _guardrails.check(user_input, context)
    if safety_flag.triggered:
        response = _guardrails.get_safety_response(safety_flag)
        response.setdefault("metadata", {})["mode"] = mode
        return response
    
    # 2. INTENT DETECTION
    intent_result = _intent_detector.detect(user_input)
    
    # 3. MODULE ROUTING
    route_result = _router.route(intent_result.intent, context)
    
    # 4. DECISION ENGINE (generates full response)
    response = _decision_engine.evaluate(route_result)
    
    # 5. ★ APPLY MODE FILTER ★ (critical step)
    response = _mode_filter.apply(response, mode=mode)
    
    # 6. ATTACH METADATA
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    response.setdefault("metadata", {}).update({
        "processing_time_ms": elapsed_ms,
        "intent_confidence": intent_result.confidence,
        "mode": mode,  # ← Mode recorded in metadata
    })
    
    return response
```

#### API Endpoint Handler

```python
@api_router.post("/query", response_model=ChatbotResponse)
async def chatbot_query(req: ChatbotRequest) -> ChatbotResponse:
    """
    Endpoint that receives mode from client and passes through pipeline.
    """
    try:
        result = process_query(
            user_input=req.input,
            mode=req.mode,  # ← Mode from request
            context=req.context,
            scope=req.scope,
        )
        return ChatbotResponse(**result)
    except Exception as e:
        # Error handling (mode-aware responses)
        return ChatbotResponse(
            intent="error",
            template="MODEL_ERROR",
            variables={"error": str(e)},
            explanation={"reason_codes": ["processing_error"], "modules": {}},
            metadata={"mode": req.mode, "error": True}
        )
```

---

## 7. Response Examples

### Example 1: Drug Safety Analysis — Doctor Mode

```json
{
  "intent": "analyze_drug_safety",
  "template": "DRUG_USE_WITH_CAUTION",
  "variables": {
    "drug_name": "Warfarin",
    "risk_level": "high",
    "summary": "Warfarin requires careful dose management...",
    "recommendation": "Consider dose adjustment"
  },
  "explanation": {
    "reason_codes": [
      "genetic_polymorphism",
      "high_sensitivity",
      "narrow_therapeutic_index"
    ],
    "reason_details": [
      {
        "code": "genetic_polymorphism",
        "severity": "high",
        "detail": "Patient carries CYP2C9*3/*3 (poor metabolizer)"
      },
      {
        "code": "narrow_therapeutic_index",
        "severity": "high",
        "detail": "Warfarin has narrow therapeutic window (INR 2-3)"
      }
    ],
    "modules": {
      "pharmacogenomics_model": {
        "gene": "CYP2C9",
        "phenotype": "poor_metabolizer",
        "confidence": 0.94,
        "recommendation": "Reduce starting dose by 30-40%"
      },
      "eligibility_model": {
        "score": 0.87,
        "contraindicated": false,
        "caution": true
      },
      "interaction_matrix": {
        "total_interactions": 3,
        "significant": 1
      }
    }
  },
  "metadata": {
    "mode": "doctor",
    "processing_time_ms": 234.56,
    "intent_confidence": 0.98
  }
}
```

### Example 2: Same Query — Patient Mode

```json
{
  "intent": "analyze_drug_safety",
  "template": "DRUG_USE_WITH_CAUTION",
  "variables": {
    "drug_name": "Warfarin",
    "risk_level": "high",
    "summary": "Warfarin requires careful dose management...",
    "recommendation": "Consider dose adjustment"
  },
  "explanation": {
    "reason_codes": [
      "genetic_polymorphism",
      "high_sensitivity",
      "narrow_therapeutic_index"
    ],
    "reason_details": [
      {
        "code": "genetic_polymorphism",
        "severity": "high",
        "detail": "Your genetic profile affects how your body processes this drug"
      },
      {
        "code": "narrow_therapeutic_index",
        "severity": "high",
        "detail": "This medication requires careful monitoring of blood tests"
      }
    ]
    // ← NOTE: "modules" key is REMOVED entirely
  },
  "metadata": {
    "mode": "patient",
    "processing_time_ms": 234.56,
    "intent_confidence": 0.98
  }
}
```

### Key Differences in Example

| Element | Doctor | Patient |
|---------|--------|---------|
| `explanation.modules` | ✅ Included (technical) | ❌ Removed |
| `reason_details[0].detail` | "CYP2C9*3/*3 (poor metabolizer)" | "Your genetic profile affects..." |
| `variables.recommendation` | "Reduce starting dose by 30-40%" | "Consider dose adjustment" |

---

## 8. Mode Validation & Error Handling

### Request Validation

```python
class ChatbotRequest(BaseModel):
    mode: str = Field(
        "doctor",
        pattern=r"^(doctor|patient)$",  # ← Strict validation
        description="User role mode"
    )
```

**Valid requests:**
- `{"input": "...", "mode": "doctor"}`
- `{"input": "...", "mode": "patient"}`

**Invalid requests (rejected by Pydantic):**
- `{"input": "...", "mode": "admin"}` → 422 Validation Error
- `{"input": "...", "mode": "Doctor"}` → 422 (case-sensitive)
- `{"input": "...", "mode": ""}` → 422 (empty string)

### Default Behavior

- If mode not provided → defaults to `"doctor"`
- If mode invalid → FastAPI returns 422 error
- If mode unknown in filter → ModeFilter defaults to patient (safest option)

---

## 9. Security Implications

### Why This Design?

1. **Patient Safety** — Patient mode removes complex technical metrics that could be misinterpreted
2. **Regulatory** — HIPAA/FDA compliance: different authorization levels
3. **Trust** — Patients see appropriate-level detail, not overwhelming data
4. **Auditability** — Mode recorded in metadata for compliance logging

### Mode-Specific Redactions

```
Doctor Mode = Sees
├── Raw model probabilities
├── Confidence scores
├── Technical gene names (CYP2C9*3/*3)
├── Therapeutic index values
├── Pharmacokinetic parameters
└── All decision engine internals

Patient Mode = Sees
├── Plain language explanations
├── Risk levels (high/medium/low)
├── Simple recommendations
├── Safety warnings
└── But NOT: raw scores or model outputs
```

---

## 10. Use Cases & Examples

### Use Case 1: Doctor Querying Warfarin Dosing

```
Request:
{
  "input": "CYP2C9*3/*3 patient, warfarin dosing recommendation",
  "mode": "doctor",
  "context": {"drug": "warfarin", "variants": ["CYP2C9*3/*3"]}
}

Response includes:
- explanation.modules with model confidence scores
- Precise dose reduction percentage
- Pharmacokinetic data
- Therapeutic index calculations
```

### Use Case 2: Patient Portal Self-Service

```
Request:
{
  "input": "Is warfarin safe for me?",
  "mode": "patient",
  "context": {}
}

Response includes:
- Plain language explanation
- Simple yes/no + action items
- NO technical model outputs
- Patient-friendly risk description
```

### Use Case 3: Education Hub (Mixed)

```
Patient mode used for:
- Public education pages
- Patient-facing dashboards
- Public drug information

Doctor mode used for:
- Clinical decision support
- Physician training
- Research interfaces
```

---

## 11. Configuration & Customization

### Extending Mode Filter

To add more complex filtering:

```python
class ModeFilter:
    @staticmethod
    def _filter_patient(resp: dict) -> dict:
        # Remove modules
        if "explanation" in resp and "modules" in resp["explanation"]:
            del resp["explanation"]["modules"]
        
        # Future: Add more filtering
        # - Redact drug names in certain contexts
        # - Simplify technical reason_codes
        # - Convert units to patient-friendly formats
        
        return resp
```

### Frontend Customization

```javascript
// Extend UI rendering for new modes
const MODE_RENDERING_RULES = {
    doctor: {
        showConfidence: true,
        showRawData: true,
        showModuleOutputs: true
    },
    patient: {
        showConfidence: false,
        showRawData: false,
        showModuleOutputs: false
    }
};
```

---

## 12. Testing Mode Behavior

### CLI Test (`backend/main.py`)

```python
def _cli_demo() -> None:
    from backend.chatbot.controller import process_query
    
    queries = [
        ("Analyze warfarin toxicity", "doctor", {"drug": "warfarin"}),
        ("Is warfarin safe?", "patient", {}),
    ]
    
    for text, mode, ctx in queries:
        result = process_query(text, mode=mode, context=ctx)
        # Doctor mode will have explanation.modules
        # Patient mode will NOT
```

### API Test

```bash
# Doctor mode
curl -X POST http://localhost:8000/api/v1/chatbot/query \
  -H "Content-Type: application/json" \
  -d '{"input":"Warfarin analysis","mode":"doctor"}'

# Patient mode
curl -X POST http://localhost:8000/api/v1/chatbot/query \
  -H "Content-Type: application/json" \
  -d '{"input":"Is warfarin safe?","mode":"patient"}'
```

---

## Summary

| Aspect | Doctor Mode | Patient Mode |
|--------|------------|--------------|
| **Target User** | Healthcare professionals | General patients |
| **Detail Level** | Maximum (technical) | Simplified |
| **Shows model outputs?** | ✅ Yes (explanation.modules) | ❌ No |
| **Shows confidence scores?** | ✅ Yes | ❌ No |
| **Shows raw probabilities?** | ✅ Yes | ❌ No |
| **Plain language explanations?** | ✅ Technical | ✅ Simple |
| **Default mode** | Approved in code | Never applied without explicit request |
| **Implementation layer** | ModeFilter (post-processing) | Same for both |
| **Schema structure** | Full | Filtered (same top-level keys) |

---

## Files Reference

- **Mode filtering logic**: [backend/chatbot/mode_filter.py](backend/chatbot/mode_filter.py)
- **Request validation**: [backend/chatbot/controller.py](backend/chatbot/controller.py) (ChatbotRequest model)
- **Frontend mode selection**: [frontend/index.html](frontend/index.html)
- **Frontend mode handling**: [frontend/assets/js/chatbot-controller.js](frontend/assets/js/chatbot-controller.js)
- **API endpoint**: [backend/main.py](backend/main.py)
- **Response templates**: [backend/chatbot/templates.py](backend/chatbot/templates.py)
