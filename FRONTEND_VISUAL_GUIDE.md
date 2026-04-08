# 🖼️ Demo UI Quick Visual Guide

## Demo Control Panel Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TheraGENOME AI                               │
│              Interactive Demo Control Panel                         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  🎯 Demo Scenarios                                                   │
│  Select a scenario to demonstrate the system's capabilities          │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │     ✓        │  │      ⚠       │  │      ⚖       │              │
│  │  Safe Case   │  │ High Risk    │  │ Compare      │              │
│  │ No drug      │  │ Genetic      │  │ Drugs        │              │
│  │ interactions │  │ contra.      │  │ comparison   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                      │
│  Display Mode: [ Doctor Mode (Full Details) ▼ ]                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 📋 Input Summary                                                    │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ Scenario: Safe Treatment Case                                 │  │
│ │ Description: Patient with no drug interactions; safe to use   │  │
│ │ Intent Detected: [ drug_analysis ]                           │  │
│ │ Processing Time: 45ms                                         │  │
│ └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 🔍 Decision Result                                                  │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ ┌─────────────────────────────┐      92.5% Confidence        │  │
│ │ │  SAFE_TO_USE   (GREEN)      │                              │  │
│ │ └─────────────────────────────┘                              │  │
│ │                                                               │  │
│ │ Risk Level: [ LOW ] (green)                                 │  │
│ │ Drug: Amoxicillin                                           │  │
│ │ Reason Codes: [ NORMAL_METABOLISM ] [ NO_INTERACTIONS ]    │  │
│ │                                                               │  │
│ │                    [ 💡 Show Explanation ]                   │  │
│ └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│ Hidden by default, expands on button click ↓                        │
│                                                                      │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ 🧠 Detailed Explanation                                       │  │
│ │                                                               │  │
│ │ Clinical Rationale:                                          │  │
│ │ ┌─────────────────────────────────────────────────────────┐ │  │
│ │ │ NORMAL_METABOLISM (Module: genetic_analysis)           │ │  │
│ │ │ Patient is normal metabolizer for CYP2D6               │ │  │
│ │ │ Severity: [ LOW ]                                       │ │  │
│ │ │                                                         │ │  │
│ │ │ NO_INTERACTIONS (Module: interaction_analysis)         │ │  │
│ │ │ No significant drug interactions detected              │ │  │
│ │ │ Severity: [ LOW ]                                       │ │  │
│ │ └─────────────────────────────────────────────────────────┘ │  │
│ │                                                               │  │
│ │ Model Details (Doctor Mode)                                 │  │
│ │ ┌─────────────────────────────────────────────────────────┐ │  │
│ │ │ Toxicity Analysis                                       │ │  │
│ │ │ {                                                       │ │  │
│ │ │   "overall_toxicity_risk": "low",                      │ │  │
│ │ │   "max_safe_dose": {...},                              │ │  │
│ │ │   "contraindications": []                              │ │  │
│ │ │ }                                                       │ │  │
│ │ └─────────────────────────────────────────────────────────┘ │  │
│ └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

For COMPARISON_RESULT template:
┌─────────────────────────────────────────────────────────────────────┐
│ ⚖ Drug Comparison                                                   │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ Drug              │ Risk Level  │ Confidence │ Status        │  │
│ ├───────────────────┼─────────────┼────────────┼───────────────┤  │
│ │ Vancomycin        │ [LOW]       │   94.2%    │ ✓ RECOMMENDED │  │
│ │ Linezolid         │ [MEDIUM]    │   87.5%    │       —       │  │
│ └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

For REPORT_READY template:
┌─────────────────────────────────────────────────────────────────────┐
│ 📄 Analysis Report                                                  │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ Summary                                                       │  │
│ │ Overall Assessment: Drug is safe for this patient           │  │
│ │ Key Findings: No genetic risk factors identified            │  │
│ │                                                               │  │
│ │ Risk Analysis                                                │  │
│ │ Risk Level: [ LOW ]                                         │  │
│ │ The patient has normal metabolizer status for CYP2D6...     │  │
│ │                                                               │  │
│ │ Decision Factors                                             │  │
│ │ • Normal protein binding profile                            │  │
│ │ • No organ dysfunction detected                            │  │
│ │ • Compatible with patient medical history                  │  │
│ └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

For SAFETY_WARNING template:
┌─────────────────────────────────────────────────────────────────────┐
│ ⚠️ Safety Alert                                                     │
│ This drug is contraindicated for this patient due to genetic risk  │
│ factors. Consult with a clinical pharmacist before prescribing.    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 📊 View Raw Response                                                │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ {                                                             │  │
│ │   "intent": "demo_run",                                       │  │
│ │   "template": "DEMO_RESULT",                                  │  │
│ │   "scenario": {                                               │  │
│ │     "id": "safe_case",                                        │  │
│ │     "name": "Safe Treatment Case",                           │  │
│ │     ...                                                       │  │
│ │   },                                                          │  │
│ │   "result": {...}                                             │  │
│ │ }                                                             │  │
│ └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ [ ↻ Run Another Demo ]                                              │
└─────────────────────────────────────────────────────────────────────┘
```

## Color Scheme

```
PRIMARY BLUE:      #0066cc  (Links, buttons, badges)
DARK BLUE:         #004499  (Headers, hover states)
LIGHT BLUE:        #e6f2ff  (Backgrounds, subtle highlights)

SUCCESS GREEN:     #28a745  (Low risk, positive states)
WARNING YELLOW:    #ffc107  (Medium risk, caution)
DANGER RED:        #dc3545  (High risk, alerts)

NEUTRAL GRAY:      #6c757d  (Text, descriptions)
LIGHT GRAY:        #f8f9fa  (Section backgrounds)
BORDER GRAY:       #e9ecef  (Dividers, borders)
```

## Risk Level Badges

```
LOW RISK
┌─────────────────┐
│ ✓ LOW           │  Green background, green text
└─────────────────┘

MEDIUM RISK
┌─────────────────┐
│ ⚠ MEDIUM        │  Yellow background, dark text
└─────────────────┘

HIGH RISK
┌─────────────────┐
│ ⚠ HIGH          │  Red background, red text
└─────────────────┘
```

## Template Badge Examples

```
SAFE_TO_USE (Green)
┌──────────────────┐
│ SAFE TO USE      │  Green border, green fill
└──────────────────┘

DRUG_USE_WITH_CAUTION (Yellow)
┌──────────────────┐
│ USE WITH CAUTION │  Yellow border, yellow fill
└──────────────────┘

DRUG_NOT_RECOMMENDED (Red)
┌──────────────────┐
│ NOT RECOMMENDED  │  Red border, red fill
└──────────────────┘
```

## Responsive Behavior

### Desktop (1200px+)
```
Full 3-column layout for buttons
Side-by-side sections
Full table width for comparisons
All features visible
```

### Tablet (768px - 1199px)
```
Grid buttons stack to 2 columns
Sections still side-by-side where possible
Table scrolls horizontally if needed
Mode selector on same line
```

### Mobile (< 768px)
```
Single column layout
Buttons stack vertically
Full-width input fields
Stacked sections (no side-by-side)
Mode selector takes full width
Touchable button sizes (min 44px height)
```

## Animation Timing

```
Button Hover:     150ms (--transition-fast)
Section Slide-in: 300ms (--transition-normal)
Spinner:          1s rotation loop
Loading Delay:    500-1500ms simulated

Smooth scroll:    smooth (CSS)
Scroll-into-view: smooth (JS)
```

## Accessibility Features

✓ Semantic HTML5 structure
✓ Aria labels for screen readers
✓ Color + text indicators (not color-only)
✓ Keyboard navigation support
✓ Sufficient contrast ratios
✓ Focus indicators
✓ Skip links (future enhancement)
✓ Alt text for icons

---

**Visual design optimized for clarity and usability.**
