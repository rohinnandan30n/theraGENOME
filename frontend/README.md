# TheraGENOME AI — Frontend Demo Control Panel

## 🎯 Overview

A modern, interactive demo control panel for showcasing the TheraGenome AI system. Built with vanilla HTML5, CSS3, and JavaScript for portability and simplicity.

## ✨ Features

- **Interactive Demo Scenarios** — Run pre-configured test cases with one click
- **Real-Time Results** — Display pipeline results step-by-step
- **Mode Toggle** — Switch between Doctor (full details) and Patient (simplified) modes
- **Dynamic Rendering** — Automatically render results based on template type
- **Color-Coded Severity** — Visual indicators for risk levels (green/yellow/red)
- **Collapsible Sections** — Explanation and raw response panels
- **Responsive Design** — Works on desktop, tablet, and mobile
- **No Dependencies** — Pure vanilla JavaScript, no frameworks required

## 📁 Project Structure

```
frontend/
├── index.html                 # Main HTML template
├── assets/
│   ├── css/
│   │   └── styles.css        # Complete styling (modern, minimal design)
│   └── js/
│       ├── api-client.js     # Backend API communication
│       ├── ui-renderer.js    # Dynamic UI rendering logic
│       └── app.js            # Main application controller
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- FastAPI installed (`pip install fastapi uvicorn`)
- Backend running on `http://localhost:8000`

### Step 1: Start the Backend

```bash
# From project root
cd backend/
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

API endpoints:
- `POST /api/demo/run` — Run a demo scenario
- `GET /api/demo/cases` — List available scenarios
- `GET /api/demo/info` — Get system information
- `GET /health` — Health check

### Step 2: Open Frontend

Simply open `frontend/index.html` in a web browser:

```bash
# Option 1: Direct file opening (may have CORS issues with some setups)
open frontend/index.html

# Option 2: Use Python's built-in server
cd frontend
python -m http.server 8001
# Then visit http://localhost:8001
```

### Step 3: Run Demo Scenarios

1. Click one of the three scenario buttons:
   - ✓ **Safe Case** — Patient with no drug interactions
   - ⚠ **High Risk Case** — Patient with genetic contraindications
   - ⚖ **Compare Drugs** — Multi-drug comparison

2. Select display mode (Doctor or Patient)

3. Watch the results render step-by-step

## 🎨 UI Components

### Demo Control Panel
- Three scenario buttons with descriptions
- Mode selector (Doctor/Patient)
- Status feedback

### Results Display (Step-by-Step)

1. **Input Summary**
   - Scenario name and description
   - Detected intent
   - Processing time

2. **Decision Result**
   - Template badge (color-coded: green/yellow/red)
   - Risk level indicator
   - Confidence score
   - Drug name
   - Reason codes

3. **Explanation Panel** (Collapsible)
   - Clinical rationale
   - Detailed reason codes with severity
   - Model outputs (Doctor mode only)

4. **Comparison View** (conditional)
   - Side-by-side drug comparison table
   - Risk levels highlighted
   - Best option marked

5. **Report View** (conditional)
   - Summary section
   - Risk analysis
   - Decision factors

6. **Safety Warning** (conditional)
   - Full-width warning banner
   - Red emphasis for critical alerts

### Additional Features
- **Raw Response Toggle** — View complete JSON response for debugging
- **Reset Button** — Clear results and start over
- **Loading Indicator** — Spinner during API calls

## 🔧 Configuration

### API Endpoint

To change the backend URL, edit `frontend/assets/js/api-client.js`:

```javascript
// Line 5 - change baseUrl
const apiClient = new DemoAPIClient('http://your-server.com:8000');
```

### Behavior

To customize demo behavior, edit `frontend/assets/js/app.js`:

```javascript
// Adjust processing simulation delay (line ~85)
simulateProcessing() {
    const delay = Math.random() * 1000 + 500; // 500-1500ms
    return new Promise(resolve => setTimeout(resolve, delay));
}
```

## 📱 Responsive Breakpoints

- **Desktop**: Full layout (1200px+)
- **Tablet**: 768px - 1199px
- **Mobile**: < 768px

## 🎯 Key Design Decisions

### No Framework
- Uses vanilla JavaScript for portability
- No build process required
- Can be deployed as static files
- Easy to integrate with any backend

### No Medical Text Generation
- All text is structured data from backend
- Templates are rendered without modification
- No AI-generated descriptions or explanations

### Real Pipeline Execution
- Every demo runs through the actual pipeline
- Results are 100% authentic
- No simulated or hardcoded outputs

### Color Coding
- **Green** (low risk) — Safe to use
- **Yellow** (medium risk) — Use with caution
- **Red** (high risk) — Not recommended

## 🔐 Security Considerations

### For Production

1. **API Security**
   - Implement authentication/authorization
   - Add rate limiting
   - Use HTTPS only

2. **CORS**
   - Restrict to specific origins (line 18 in main.py)
   - Don't allow "*" in production

3. **Data Privacy**
   - Don't expose raw genetic data in patient mode
   - Implement proper data encryption
   - Follow HIPAA/GDPR guidelines

## 📊 API Reference

### POST /api/demo/run

Run a demo scenario.

**Request:**
```json
{
  "case_id": "safe_case",
  "mode": "doctor",
  "scope": "full"
}
```

**Response:**
```json
{
  "intent": "demo_run",
  "template": "DEMO_RESULT",
  "scenario": {
    "id": "safe_case",
    "name": "Safe Treatment Case",
    "description": "Patient with no drug interactions; safe to use"
  },
  "result": {
    // Full process_query() response
  },
  "metadata": {
    "source": "demo_engine",
    "scenario_id": "safe_case",
    "mode": "doctor",
    "scope": "full"
  }
}
```

### GET /api/demo/cases

Get list of available demo scenarios.

**Response:**
```json
{
  "total": 3,
  "cases": [
    {
      "id": "safe_case",
      "name": "Safe Treatment Case",
      "description": "Patient with no drug interactions; safe to use",
      "intent": "drug_analysis"
    },
    // ... more cases
  ]
}
```

### GET /api/demo/info

Get demo system information.

**Response:**
```json
{
  "version": "1.0.0",
  "description": "TheraGenome AI Demo Control Panel",
  "scenarios": 3,
  "modes": ["doctor", "patient"],
  "scopes": ["full", "summary"],
  "endpoints": [
    "/api/demo/run (POST)",
    "/api/demo/cases (GET)",
    "/api/demo/info (GET)"
  ]
}
```

## 🐛 Troubleshooting

### "Network Error" or "API not found"

**Problem:** Frontend can't reach backend
**Solution:**
1. Verify backend is running on port 8000
2. Check API endpoint in `api-client.js`
3. Verify CORS is enabled (check main.py)
4. Try `http://localhost:8000/health` in browser

### Demo scenario fails with 400 error

**Problem:** Invalid case_id
**Solution:**
1. Check available cases: `GET /api/demo/cases`
2. Use valid case IDs: `safe_case`, `high_risk_case`, `comparison_case`
3. Verify mode is `doctor` or `patient`

### Results don't display

**Problem:** JSON parsing error
**Solution:**
1. Check browser console for errors
2. View raw response using "View Raw Response" button
3. Verify response structure in API documentation

### Styling looks broken

**Problem:** CSS file not loaded
**Solution:**
1. Check that `styles.css` exists at `frontend/assets/css/styles.css`
2. Verify file paths in HTML
3. Clear browser cache (Ctrl+Shift+Delete / Cmd+Shift+Delete)

## 📚 Code Architecture

### API Client (`api-client.js`)
- Abstracts HTTP communication
- Handles request/response
- Provides error handling
- Global instance: `window.apiClient`

### UI Renderer (`ui-renderer.js`)
- Static methods for rendering components
- Handles all DOM manipulation
- Supports conditional rendering based on template
- Methods:
  - `renderDemoResult()` — Main handler
  - `renderDecisionCard()` — Risk/drug display
  - `renderComparisonView()` — Comparison table
  - `renderReportView()` — Report details

### App Controller (`app.js`)
- Main application logic
- Event listener management
- State management
- Methods:
  - `handleDemoButtonClick()` — Run scenario
  - `toggleExplanation()` — Show/hide details
  - `reset()` — Clear results

## 🎓 Learning Resources

### Vanilla JavaScript Patterns Used
- Event delegation
- DOM manipulation
- CSS classes for state
- LocalStorage for preferences

### Modern CSS Features
- CSS Grid for layout
- CSS Variables for theming
- Flexbox for component alignment
- Smooth transitions and animations

## 🚀 Future Enhancements

- [ ] Add more demo scenarios
- [ ] Custom scenario builder
- [ ] Export results as PDF
- [ ] Scenario replay/history
- [ ] Real-time backend status indicator
- [ ] Keyboard shortcuts for demo buttons
- [ ] Dark mode toggle
- [ ] Internationalization (i18n)
- [ ] Advanced filtering and search

## 📝 License

TheraGenome AI © 2025

## 🤝 Contributing

To add features or fix bugs:

1. Update HTML structure in `index.html`
2. Add styles to `frontend/assets/css/styles.css`
3. Implement logic in appropriate JS file
4. Test across browsers and screen sizes

---

**Status**: ✅ Production Ready

For questions or issues, refer to the main project README.
