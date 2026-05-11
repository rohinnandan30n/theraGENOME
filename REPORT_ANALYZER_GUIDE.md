# Medical Report Analyzer — Implementation Guide

## 🎯 Feature Overview

The **Medical Report Analyzer** is a new feature within TheraGenome AI that enables:

- **Patient Mode**: Upload medical reports to get simple, detailed explanations of test results
- **Doctor Mode**: Upload reports/test results to analyze comprehensive clinical data with graphs, abnormality detection, organ involvement assessment, and drug interaction risk

---

## 📁 Files Created

### Backend

1. **`backend/chatbot/report_analyzer.py`** (450+ lines)
   - Core analysis engine
   - Text extraction and parsing
   - Test value classification (normal/low/high/critical)
   - Abnormality detection algorithms
   - Organ system mapping
   - Trend analysis across multiple reports
   - Mode-specific response generation

2. **`backend/chatbot/report_api.py`** (400+ lines)
   - FastAPI router for report uploads
   - Document extraction (PDF + OCR for images)
   - File validation and sanitization
   - Multi-report comparison endpoint
   - Two main endpoints:
     - `POST /api/v1/reports/upload` — Single report analysis
     - `POST /api/v1/reports/compare` — Trend detection across reports

### Frontend

3. **`frontend/reports.html`** (800+ lines)
   - Complete UI for report upload and analysis
   - Drag-and-drop upload interface
   - Mode selector (Doctor/Patient toggle)
   - Tabbed results display (Summary/Tests/Analysis/Integration)
   - Responsive glass-morphism design
   - Real-time file preview

### Integration Updates

4. **`backend/main.py`** — Updated to include report router
5. **`frontend/index.html`** — Added "📊 Reports" navigation link
6. **`frontend/education.html`** — Added "📊 Report Analyzer" tab
7. **`frontend/simulator/index.html`** — Added "📊 Reports" navigation

---

## 🔧 Backend Architecture

### ReportAnalyzer Class

**Location**: `backend/chatbot/report_analyzer.py`

```python
class ReportAnalyzer:
    def parse(text, report_type, confidence_score) → ParsedReport
    def analyze_trends(reports) → dict
    def generate_patient_summary(report) → str
    def generate_doctor_analysis(report) → dict
```

**Core Functions**:
- `_extract_test_values()` — Parse lab values from text using regex + reference database
- `_classify_abnormality()` — Determine if value is normal/low/high/critical
- `_correlate_to_organs()` — Map abnormal tests to affected organs
- `_assess_drug_interactions()` — Flag liver/kidney concerns
- `_generate_clinical_recommendations()` — Suggest next steps

**Reference Ranges Database** (60+ common tests):
- Blood work (CBC, CMP, LFTs)
- Thyroid markers (TSH, T3, T4)
- Metabolic markers (glucose, A1C, lipids)
- Electrolytes
- Cardiac markers
- And more...

### DocumentExtractor Class

**Location**: `backend/chatbot/report_api.py`

```python
class DocumentExtractor:
    @staticmethod
    def extract_from_pdf(file_content) → str  # PyMuPDF
    @staticmethod
    def extract_from_image(file_content) → str  # Tesseract OCR
```

**Supported Formats**:
- ✅ PDF files → PyMuPDF (fitz)
- ✅ PNG, JPG → Tesseract OCR + PIL
- ✅ Up to 50 MB file size

### API Endpoints

**Base**: `POST /api/v1/reports/`

| Endpoint | Method | Purpose | Returns |
|----------|--------|---------|---------|
| `/upload` | POST | Analyze single report | ReportAnalysisResponse |
| `/compare` | POST | Compare multiple reports | Trend analysis |
| `/supported-formats` | GET | List formats | Format metadata |

#### POST /api/v1/reports/upload

**Request**:
```json
{
  "file": <binary PDF/image>,
  "mode": "doctor|patient",
  "report_type": "blood_work|imaging|cardiac|etc"
}
```

**Response (Doctor Mode)**:
```json
{
  "success": true,
  "mode": "doctor",
  "report_type": "blood_work",
  "date_of_report": "2026-04-09",
  "patient_name": "John Doe",
  "summary": "Report summary...",
  "data": {
    "tests": [...],
    "analysis": {
      "test_summary": {...},
      "critical_findings": [...],
      "organ_involvement": {...},
      "drug_interaction_risk": {...},
      "recommendations": [...]
    }
  },
  "confidence": 0.85
}
```

**Response (Patient Mode)**:
```json
{
  "success": true,
  "mode": "patient",
  "summary": "Your lab results show...",
  "data": {
    "tests": [...],
    "test_counts": {
      "normal": 8,
      "abnormal": 2,
      "critical": 0
    }
  },
  "confidence": 0.85
}
```

---

## 🎨 Frontend Architecture

### ReportAnalyzerUI Class

**Location**: `frontend/reports.html` (embedded in script)

```javascript
class ReportAnalyzerUI {
    mode = 'doctor'  // Persisted to localStorage
    currentReport = null
    selectedFile = null
    
    setMode(mode)           // Switch doctor/patient
    handleFiles(files)      // Drag-drop handler
    analyzeReport()         // Call backend API
    displayResults(report)  // Render response
    switchTab(tab)          // Tab navigation
    goToSimulator()         // Integration link
    goToEducation()         // Integration link
}
```

### UI Sections

1. **Upload Zone**
   - Drag-and-drop interface
   - File validation
   - File preview display
   - Max 50 MB

2. **Results Tabs**
   - **Summary** — Plain text for patients, structured for doctors
   - **Test Results** — Table with value, reference, status badges
   - **Clinical Analysis** — Doctor-mode only analysis
   - **Next Steps** — Integration buttons

3. **Test Results Table**
   - Test Name
   - Value + Unit
   - Reference Range
   - Status Badge (color-coded: green/blue/orange/red)

4. **Doctor-Only Analysis** (Auto-hidden in patient mode)
   - Test summary statistics
   - Critical findings with deviation %
   - Organ involvement mapping
   - Drug interaction risk assessment
   - Clinical recommendations

### Styling System

**Colors**:
- Status Normal: Green (#22c55e)
- Status Low: Blue (#60a5fa)
- Status High: Orange (var(--accent))
- Status Critical: Red (var(--danger))

**Responsive Design**:
- Desktop: 2-column grid (upload + results)
- Tablet: 1-column stacked
- Mobile: Full-width responsive

---

## 📊 Data Flow

### Single Report Analysis

```
User selects Doctor/Patient mode
    ↓
Uploads PDF or Image file
    ↓
Frontend validates file type & size
    ↓
POST to /api/v1/reports/upload with FormData
    ↓
Backend extracts text (PyMuPDF or Tesseract)
    ↓
ReportAnalyzer.parse() extracts test values
    ↓
Reference ranges matched → abnormality classified
    ↓
Mode-specific response generated:
    - Patient: Plain language summary
    - Doctor: Full clinical analysis
    ↓
Frontend displays results (tab-separated)
```

### Multi-Report Comparison

```
User uploads 2+ reports
    ↓
POST to /api/v1/reports/compare
    ↓
Each report parsed independently
    ↓
ReportAnalyzer.analyze_trends() correlates:
    - Test values across dates
    - Trend direction (increasing/decreasing)
    - Percent change calculation
    ↓
Returns trend object with historical context
```

### Integration Paths

**To Drug Simulator**:
- Report data saved to sessionStorage
- User clicks "Use in Drug Simulator"
- Redirects to simulator/index.html
- Simulator loads report data for context

**To Education Hub**:
- Links to education.html
- User can review relevant genes/organs
- Come back to continue report analysis

---

## 🚀 Installation & Dependencies

### Python Packages Needed

```bash
pip install pymupdf          # PDF extraction (fitz)
pip install pytesseract      # OCR for images
pip install pillow           # Image processing
```

### System Dependencies

**For Windows**:
```bash
# Install Tesseract OCR
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Then set path in code: pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**For Linux**:
```bash
sudo apt-get install tesseract-ocr
```

**For macOS**:
```bash
brew install tesseract
```

---

## 📋 Data Models

### LabValue
```python
@dataclass
class LabValue:
    test_name: str           # "hemoglobin"
    value: float             # 14.5
    unit: str                # "g/dL"
    reference_min: float     # 13.5
    reference_max: float     # 17.5
    abnormality: AbnormalityLevel  # "normal"/"low"/"high"/"critical"
    reference_range: str     # "13.5-17.5"
    date_tested: str         # ISO format
```

### ParsedReport
```python
@dataclass
class ParsedReport:
    patient_name: str | None
    date_of_report: str
    tests: list[LabValue]
    report_type: str         # "blood_work", "imaging", etc
    raw_text: str | None     # For debugging
    confidence_score: float  # 0-1 extraction confidence
```

### ReportAnalysisResponse (API)
```python
class ReportAnalysisResponse(BaseModel):
    success: bool
    mode: str                # "doctor" or "patient"
    report_type: str
    date_of_report: str
    patient_name: str | None
    summary: str             # Mode-specific text
    data: dict[str, Any]     # Full parsed data
    confidence: float
    message: str
```

---

## 🔍 Reference Ranges Database

**Coverage**: 60+ common laboratory tests

**Categories**:
- ✅ Complete Blood Count (CBC): WBC, RBC, Hemoglobin, Hematocrit, Platelets
- ✅ Metabolic Panel (CMP): Glucose, Electrolytes, BUN, Creatinine
- ✅ Liver Function Tests (LFTs): ALT, AST, Bilirubin, ALP
- ✅ Lipid Panel: Cholesterol, HDL, LDL, Triglycerides
- ✅ Thyroid Panel: TSH, T3, T4
- ✅ Additional: A1C, and more

**Format**:
```python
REFERENCE_RANGES = {
    "test_name": {
        "min": 4.5,
        "max": 11.0,
        "unit": "k/uL"
    },
    ...
}
```

---

## 🎯 Abnormality Classification Algorithm

**How severity is determined**:
```
IF value is within [min, max]
    → Status = NORMAL

ELSE IF value < min
    deviation = (min - value) / min
ELSE IF value > max
    deviation = (value - max) / max

IF deviation > 0.25 (25% outside range)
    → Status = CRITICAL
ELSE IF deviation > 0.10 (10% outside range)
    → Status = HIGH or LOW
ELSE
    → Status = HIGH or LOW (minor)
```

**Example**:
- Normal range: 4.5-11.0 k/uL
- Value: 3.0 (below normal)
- Deviation: (4.5 - 3.0) / 4.5 = 33%
- **Status**: CRITICAL (33% > 25%)

---

## 🏥 Organ Involvement Mapping

**Organs mapped** (based on test abnormalities):
- **Liver**: ALT, AST, Bilirubin, ALP
- **Kidney**: Creatinine, BUN
- **Thyroid**: TSH, T3, T4
- **Blood**: WBC, RBC, Hemoglobin, Hematocrit, Platelets
- **Metabolism**: Glucose, A1C, Cholesterol, Triglycerides
- **Electrolytes**: Sodium, Potassium, Chloride

**Use Case**: When abnormal tests detected → automatically identifies which organs are involved

---

## 💊 Drug Interaction Risk Assessment

**Flags set if abnormal values detected in**:
- **Liver**: ALT, AST, Bilirubin
- **Kidney**: Creatinine, BUN

**Risk Levels**:
- **HIGH**: Both liver AND kidney concerns
- **MEDIUM**: Either liver OR kidney concern
- **LOW**: No concerns

**Clinical Implication**: Abnormal liver/kidney function suggests reduced drug metabolism → higher toxicity risk

---

## 📈 Multi-Report Trend Analysis

**Supported Metrics**:
- Direction of trend (increasing/decreasing)
- Percent change over time
- Number of reports compared
- Date range (earliest to latest)

**Example Output**:
```json
{
  "hemoglobin": {
    "direction": "decreasing",
    "change_percent": -12.5,
    "first_value": 14.5,
    "last_value": 12.7,
    "count": 3
  }
}
```

---

## 🔐 Security & Privacy

**File Handling**:
- Files uploaded temporarily in memory
- Matched against MIME types (PDF, PNG, JPG only)
- Max file size: 50 MB
- Not persisted to disk by default

**Data Extraction**:
- OCR results not logged
- Patient names extracted but not stored persistently
- All processing server-side (not exposed to client)

**Mode Validation**:
- Strict regex validation: `^(doctor|patient)$`
- Invalid modes default to patient (safest)
- Mode recorded in response metadata

---

## 🧪 Testing the Reports Feature

### Start Servers

```bash
# Backend (from project root)
cd c:\Users\shiva\Desktop\Integration-theragenome2
python3.11 -m uvicorn backend.main:app --host localhost --port 8000 --reload

# Frontend (in another terminal)
cd c:\Users\shiva\Desktop\Integration-theragenome2\frontend
python3.11 -m http.server 8001
```

### Access UI

```
http://localhost:8001/reports.html
```

### Manual Testing Workflow

1. **Select Patient Mode**
   - Click "👤 Patient" button
   - Upload a test report (PDF or image)
   - Click "🔬 Analyze Report"
   - View plain-language summary

2. **Select Doctor Mode**
   - Click "👨‍⚕️ Doctor" button
   - Upload same report
   - Click tabs: Summary → Test Results → Clinical Analysis
   - View full analysis with organ mapping

3. **Integration Test**
   - Click "Use in Drug Simulator" button
   - Should redirect to simulator with report data

4. **Navigation Test**
   - From Chatbot → click "📊 Reports"
   - From Reports → click "← Back to Chatbot"
   - From Education → click "📊 Report Analyzer"
   - From Simulator → click "📊 Reports"

---

## 📝 Example Report Analysis

### Input: Blood Test Image
```
Patient: Jane Smith
Date: 2026-04-08

WHITE BLOOD CELL: 12.5 k/uL
RED BLOOD CELL: 4.2 M/uL
HEMOGLOBIN: 13.0 g/dL
GLUCOSE: 145 mg/dL
CREATININE: 1.8 mg/dL
ALT: 75 IU/L
```

### Patient Mode Response

```
Report Date: 2026-04-08
Tests Performed: 6

⚠️ CRITICAL VALUES (1):
  • creatinine: 1.8 mg/dL (Normal: 0.7-1.3 mg/dL)

⚡ ABNORMAL VALUES (3):
  • white blood cell count: 12.5 k/uL (higher than normal)
  • glucose: 145 mg/dL (higher than normal)
  • alanine aminotransferase: 75 IU/L (higher than normal)

✅ NORMAL VALUES: 2 tests within normal range
```

### Doctor Mode Response

```
📊 Test Summary
Total Tests: 6 | Normal: 2 | Abnormal: 3 | Critical: 1

⚠️ Critical Findings
- creatinine: 1.8 mg/dL
  Ref: 0.7-1.3 | Deviation: 38.5%

- glucose: 145 mg/dL
  Ref: 70-100 | Deviation: 45%

🏥 Organ Involvement
- kidney: creatinine
- metabolism: glucose

💊 Drug Interaction Assessment
Liver: ⚠️ Concern (elevated ALT)
Kidney: ⚠️ Concern (elevated creatinine)
Overall Risk: HIGH

📋 Clinical Recommendations
✓ Nephrology consultation advised
✓ Consider endocrinology referral for glucose management
```

---

## 🚦 Current Status

**✅ Implemented**:
- Backend ReportAnalyzer engine
- FastAPI upload endpoints
- PDF + image extraction
- Frontend UI with mode switching
- Results display (tabs, tables, badges)
- Doctor-mode analysis
- Navigation integration
- Responsive design

**⏳ Ready for Next Phase**:
- Chart.js visualization (line charts, heatmaps)
- Advanced trend comparison UI
- Report history storage (optional)
- Export functionality (PDF reports)
- AI-powered recommendations enhancement

---

## 🔗 Integration Points

1. **Chatbot** (index.html)
   - New "📊 Reports" nav button
   - User can upload reports and get analysis

2. **Education Hub** (education.html)
   - New "📊 Report Analyzer" tab
   - User can review relevant genes after report analysis

3. **3D Simulator** (simulator/index.html)
   - New "📊 Reports" nav button
   - Can use report data for drug interaction context
   - Pre-fill organ selections based on report

---

## 📞 API Quick Reference

### Upload & Analyze

```bash
curl -X POST http://localhost:8000/api/v1/reports/upload \
  -F "file=@myreport.pdf" \
  -F "mode=doctor" \
  -F "report_type=blood_work"
```

### Get Supported Formats

```bash
curl http://localhost:8000/api/v1/reports/supported-formats
```

### Compare Multiple Reports

```bash
curl -X POST http://localhost:8000/api/v1/reports/compare \
  -F "files=@report1.pdf" \
  -F "files=@report2.pdf" \
  -F "mode=doctor"
```

---

## 🎓 Next Steps (Future Enhancements)

1. **Visualization Layer**
   - Line charts for trends
   - Heatmaps for multi-parameter analysis
   - Bar charts for abnormality distribution

2. **Storage & History**
   - Persistent report storage (optional)
   - User report history
   - Comparison across years

3. **AI Enhancement**
   - LLM-powered clinical insights
   - Personalized recommendations
   - Risk prediction models

4. **Export & Sharing**
   - PDF report generation
   - Data export (CSV)
   - Report sharing links

5. **Integration**
   - FDA 21 CFR Part 11 compliance
   - HL7/FHIR interoperability
   - EHR system integration

---

## 📚 References

- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [FastAPI File Upload](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Chart.js Documentation](https://www.chartjs.org/)
