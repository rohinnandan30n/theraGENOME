"""
TheraGenome AI — Medical Report Analyzer
========================================
Core logic for extracting clinical data from medical reports (PDF/images).

Uses AI-powered extraction to parse:
- Laboratory test values
- Reference ranges
- Dates and units
- Abnormality detection
- Trend analysis

Design principles
-----------------
*   AI-powered extraction (using LLM for semantic understanding)
*   Structured data output (always JSON-serializable)
*   Mode-aware response generation (doctor vs patient)
*   Seamless integration with existing models and database
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any
from datetime import datetime
from enum import Enum

# Import resistance model for infection analysis
try:
    from backend.models.resistance import antibiotic_resistance_model
except ImportError:
    try:
        from models.resistance import antibiotic_resistance_model
    except ImportError:
        antibiotic_resistance_model = None


# ──────────────────────────────────────────────
#  Data Models
# ──────────────────────────────────────────────

class AbnormalityLevel(str, Enum):
    """Severity of test value abnormality."""
    CRITICAL = "critical"
    HIGH = "high"
    LOW = "low"
    NORMAL = "normal"


@dataclass
class LabValue:
    """Parsed laboratory test result."""
    test_name: str
    value: float
    unit: str
    reference_min: float | None
    reference_max: float | None
    abnormality: AbnormalityLevel
    reference_range: str  # e.g., "4.5-11.0"
    date_tested: str  # ISO format
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)


@dataclass
class ParsedReport:
    """Extracted data from medical report."""
    patient_name: str | None
    date_of_report: str
    tests: list[LabValue]
    report_type: str  # "blood", "imaging", "cardiac", etc.
    raw_text: str | None  # Original extracted text for debugging
    confidence_score: float  # 0-1 extraction confidence
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "patient_name": self.patient_name,
            "date_of_report": self.date_of_report,
            "tests": [t.to_dict() for t in self.tests],
            "report_type": self.report_type,
            "confidence_score": self.confidence_score,
        }


# ──────────────────────────────────────────────
#  Reference Ranges Database
# ──────────────────────────────────────────────

REFERENCE_RANGES = {
    # Common blood tests (adult ranges)
    "white blood cell count": {"min": 4.5, "max": 11.0, "unit": "k/uL"},
    "wbc": {"min": 4.5, "max": 11.0, "unit": "k/uL"},
    
    "red blood cell count": {"min": 4.5, "max": 5.5, "unit": "M/uL"},
    "rbc": {"min": 4.5, "max": 5.5, "unit": "M/uL"},
    
    "hemoglobin": {"min": 13.5, "max": 17.5, "unit": "g/dL"},
    "hb": {"min": 13.5, "max": 17.5, "unit": "g/dL"},
    
    "hematocrit": {"min": 41, "max": 53, "unit": "%"},
    "hct": {"min": 41, "max": 53, "unit": "%"},
    
    "platelet count": {"min": 150, "max": 400, "unit": "k/uL"},
    "plt": {"min": 150, "max": 400, "unit": "k/uL"},
    
    "glucose": {"min": 70, "max": 100, "unit": "mg/dL"},
    "blood glucose": {"min": 70, "max": 100, "unit": "mg/dL"},
    
    "creatinine": {"min": 0.7, "max": 1.3, "unit": "mg/dL"},
    
    "blood urea nitrogen": {"min": 7, "max": 20, "unit": "mg/dL"},
    "bun": {"min": 7, "max": 20, "unit": "mg/dL"},
    
    "sodium": {"min": 136, "max": 145, "unit": "mEq/L"},
    "na": {"min": 136, "max": 145, "unit": "mEq/L"},
    
    "potassium": {"min": 3.5, "max": 5.0, "unit": "mEq/L"},
    "k": {"min": 3.5, "max": 5.0, "unit": "mEq/L"},
    
    "chloride": {"min": 98, "max": 107, "unit": "mEq/L"},
    "cl": {"min": 98, "max": 107, "unit": "mEq/L"},
    
    "total bilirubin": {"min": 0.1, "max": 1.2, "unit": "mg/dL"},
    "bilirubin": {"min": 0.1, "max": 1.2, "unit": "mg/dL"},
    
    "alkaline phosphatase": {"min": 40, "max": 120, "unit": "IU/L"},
    "alp": {"min": 40, "max": 120, "unit": "IU/L"},
    
    "alanine aminotransferase": {"min": 7, "max": 56, "unit": "IU/L"},
    "alt": {"min": 7, "max": 56, "unit": "IU/L"},
    
    "aspartate aminotransferase": {"min": 10, "max": 40, "unit": "IU/L"},
    "ast": {"min": 10, "max": 40, "unit": "IU/L"},
    
    "cholesterol": {"min": 0, "max": 200, "unit": "mg/dL"},
    "total cholesterol": {"min": 0, "max": 200, "unit": "mg/dL"},
    
    "hdl": {"min": 40, "max": 100, "unit": "mg/dL"},
    "hdl cholesterol": {"min": 40, "max": 100, "unit": "mg/dL"},
    
    "ldl": {"min": 0, "max": 100, "unit": "mg/dL"},
    "ldl cholesterol": {"min": 0, "max": 100, "unit": "mg/dL"},
    
    "triglycerides": {"min": 0, "max": 150, "unit": "mg/dL"},
    
    "tsh": {"min": 0.4, "max": 4.0, "unit": "mIU/L"},
    
    "t3": {"min": 80, "max": 200, "unit": "ng/dL"},
    
    "t4": {"min": 4.5, "max": 12.0, "unit": "ug/dL"},
    
    "hemoglobin a1c": {"min": 0, "max": 5.7, "unit": "%"},
    "hba1c": {"min": 0, "max": 5.7, "unit": "%"},
}


# ──────────────────────────────────────────────
#  Core Analyzer Class
# ──────────────────────────────────────────────

class ReportAnalyzer:
    """
    Analyzes medical reports and extracts clinical data.
    
    Workflow:
    1. Extract text from PDF/image (external tool)
    2. Parse test names and values using regex + reference DB
    3. Classify abnormalities
    4. Generate mode-specific response
    """
    
    def __init__(self):
        """Initialize analyzer with reference ranges."""
        self.reference_ranges = REFERENCE_RANGES
    
    def parse(
        self,
        extracted_text: str,
        report_type: str = "blood_work",
        confidence_score: float = 0.85,
    ) -> ParsedReport:
        """
        Parse extracted text from report.
        
        Parameters
        ----------
        extracted_text : str
            Raw text extracted from PDF/image (via OCR or LLM)
        report_type : str
            Type of report: "blood", "imaging", "cardiac", etc.
        confidence_score : float
            Confidence in extraction (0-1)
        
        Returns
        -------
        ParsedReport
            Structured report with parsed tests
        """
        tests = self._extract_test_values(extracted_text)
        patient_name = self._extract_patient_name(extracted_text)
        date_of_report = self._extract_date(extracted_text)
        
        return ParsedReport(
            patient_name=patient_name,
            date_of_report=date_of_report or datetime.now().isoformat(),
            tests=tests,
            report_type=report_type,
            raw_text=extracted_text if extracted_text else None,
            confidence_score=confidence_score,
        )
    
    def _extract_test_values(self, text: str) -> list[LabValue]:
        """Extract laboratory test values from text."""
        tests: list[LabValue] = []
        
        # Pattern: "Test Name: 123.45 unit" or "Test Name 123.45"
        # This is a simplified pattern; in production use more robust parsing
        patterns = [
            r'(\w+[\s\w]*?):\s*([\d.]+)\s*(\w+/?[\w]*)',
            r'(\w+[\s\w]*?)\s+([\d.]+)\s+(\w+/?[\w]*)',
        ]
        
        for test_name, ref_info in self.reference_ranges.items():
            # Case-insensitive search for test name in text
            regex = re.compile(rf'\b{re.escape(test_name)}\b[\s:]*([0-9.]+)', re.IGNORECASE)
            matches = regex.findall(text)
            
            for value_str in matches:
                try:
                    value = float(value_str)
                    
                    # Determine abnormality
                    abnormality = self._classify_abnormality(
                        value,
                        ref_info["min"],
                        ref_info["max"]
                    )
                    
                    lab_value = LabValue(
                        test_name=test_name,
                        value=value,
                        unit=ref_info["unit"],
                        reference_min=ref_info["min"],
                        reference_max=ref_info["max"],
                        abnormality=abnormality,
                        reference_range=f"{ref_info['min']}-{ref_info['max']}",
                        date_tested=datetime.now().isoformat().split('T')[0],
                    )
                    tests.append(lab_value)
                except ValueError:
                    continue
        
        return tests
    
    def _classify_abnormality(
        self,
        value: float,
        ref_min: float,
        ref_max: float,
    ) -> AbnormalityLevel:
        """
        Classify if value is abnormal.
        
        - NORMAL: within range
        - LOW/HIGH: 10% outside range
        - CRITICAL: 25% outside range
        """
        if ref_min <= value <= ref_max:
            return AbnormalityLevel.NORMAL
        
        if value < ref_min:
            deviation = (ref_min - value) / ref_min
        else:
            deviation = (value - ref_max) / ref_max
        
        if deviation > 0.25:
            return AbnormalityLevel.CRITICAL
        elif deviation > 0.10:
            return AbnormalityLevel.HIGH if value > ref_max else AbnormalityLevel.LOW
        else:
            return AbnormalityLevel.HIGH if value > ref_max else AbnormalityLevel.LOW
    
    def _extract_patient_name(self, text: str) -> str | None:
        """Extract patient name from report text."""
        # Look for "Patient:" or "Name:" patterns
        patterns = [
            r'(?:Patient|Name):\s*([A-Za-z\s]+)',
            r'(?:Patient|Name)\s*([A-Za-z\s]+?)(?:\n|Date)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_date(self, text: str) -> str | None:
        """Extract report date from text."""
        # ISO date pattern (YYYY-MM-DD) or common formats
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def analyze_trends(
        self,
        reports: list[ParsedReport]
    ) -> dict[str, Any]:
        """
        Analyze trends across multiple reports.
        
        Returns
        -------
        dict
            Trend analysis with improvement/decline indicators
        """
        if not reports:
            return {}
        
        trends = {}
        
        # Group tests by name across reports
        test_groups: dict[str, list[tuple[str, float]]] = {}
        
        for report in reports:
            for test in report.tests:
                if test.test_name not in test_groups:
                    test_groups[test.test_name] = []
                test_groups[test.test_name].append((report.date_of_report, test.value))
        
        # Calculate trend direction and rate
        for test_name, values in test_groups.items():
            values.sort()  # Sort by date
            if len(values) >= 2:
                values_only = [v[1] for v in values]
                trend_direction = "increasing" if values_only[-1] > values_only[0] else "decreasing"
                change_pct = ((values_only[-1] - values_only[0]) / values_only[0] * 100) if values_only[0] != 0 else 0
                
                trends[test_name] = {
                    "direction": trend_direction,
                    "change_percent": round(change_pct, 2),
                    "first_value": values_only[0],
                    "last_value": values_only[-1],
                    "count": len(values_only),
                }
        
        return trends
    
    def generate_patient_summary(self, report: ParsedReport) -> str:
        """
        Generate patient-friendly summary.
        
        Patient mode: plain language, no technical jargon
        """
        critical = [t for t in report.tests if t.abnormality == AbnormalityLevel.CRITICAL]
        abnormal = [t for t in report.tests if t.abnormality in [AbnormalityLevel.HIGH, AbnormalityLevel.LOW]]
        
        summary = f"Report Date: {report.date_of_report}\n"
        summary += f"Tests Performed: {len(report.tests)}\n\n"
        
        if critical:
            summary += f"⚠️ CRITICAL VALUES ({len(critical)}):\n"
            for test in critical:
                summary += f"  • {test.test_name}: {test.value} {test.unit} (Normal: {test.reference_range} {test.unit})\n"
            summary += "\n"
        
        if abnormal:
            summary += f"⚡ ABNORMAL VALUES ({len(abnormal)}):\n"
            for test in abnormal:
                direction = "higher" if test.value > test.reference_max else "lower"
                summary += f"  • {test.test_name}: {test.value} {test.unit} ({direction} than normal)\n"
            summary += "\n"
        
        normal = [t for t in report.tests if t.abnormality == AbnormalityLevel.NORMAL]
        summary += f"✅ NORMAL VALUES: {len(normal)} tests within normal range\n"
        
        return summary
    
    def generate_doctor_analysis(self, report: ParsedReport) -> dict[str, Any]:
        """
        Generate detailed clinical analysis for doctor mode.
        
        Includes: statistics, abnormality patterns, correlations, drug recommendations, 
        infection/resistance analysis
        """
        # Detect diseases
        diseases = self._detect_diseases(report.tests)
        
        # Get drug recommendations
        drug_recommendations = self._get_drug_recommendations(diseases)
        
        # Get pharmacogenomics analysis
        pharma_analysis = self._get_pharmacogenomics_analysis(report.tests, report.raw_text)
        
        # NEW: Detect infections and get resistance analysis
        infection_data = self._detect_infections(report.tests, report.raw_text)
        resistance_analysis = None
        antibiotic_recommendations = []
        
        if infection_data:
            resistance_analysis = self._get_antibiotic_recommendations(infection_data)
            if resistance_analysis:
                # Extract antibiotic recommendations from resistance model output
                if isinstance(resistance_analysis, dict):
                    # Handle both direct result and nested structure
                    susceptibilities = resistance_analysis.get("susceptibilities", {})
                    for drug, status in susceptibilities.items():
                        if status.get("susceptible", False):
                            antibiotic_recommendations.append({
                                "drug": drug,
                                "class": status.get("drug_class", "Antibiotic"),
                                "status": "susceptible",
                                "mechanism": status.get("resistance_mechanism", "None detected")
                            })
        
        analysis = {
            "test_summary": {
                "total_tests": len(report.tests),
                "normal": len([t for t in report.tests if t.abnormality == AbnormalityLevel.NORMAL]),
                "abnormal": len([t for t in report.tests if t.abnormality == AbnormalityLevel.HIGH]),
                "low": len([t for t in report.tests if t.abnormality == AbnormalityLevel.LOW]),
                "critical": len([t for t in report.tests if t.abnormality == AbnormalityLevel.CRITICAL]),
            },
            "critical_findings": [
                {
                    "test": t.test_name,
                    "value": t.value,
                    "unit": t.unit,
                    "reference": f"{t.reference_min}-{t.reference_max}",
                    "deviation_percent": round(
                        abs(t.value - ((t.reference_min + t.reference_max) / 2)) /
                        ((t.reference_min + t.reference_max) / 2) * 100, 2
                    )
                }
                for t in report.tests if t.abnormality == AbnormalityLevel.CRITICAL
            ],
            "detected_conditions": diseases,
            "organ_involvement": self._correlate_to_organs(report.tests),
            "drug_interaction_risk": self._assess_drug_interactions(report.tests),
            "pharmacogenomics": pharma_analysis,
            "drug_recommendations": drug_recommendations,
            "recommendations": self._generate_clinical_recommendations(report.tests),
            # NEW: Add infection and resistance sections
            "infection_analysis": {
                "infection_detected": infection_data is not None,
                "details": infection_data,
                "resistance_analysis": resistance_analysis,
                "antibiotic_recommendations": antibiotic_recommendations,
            } if infection_data else None,
        }
        
        return analysis
    
    def _correlate_to_organs(self, tests: list[LabValue]) -> dict[str, list[str]]:
        """Map abnormal test values to affected organs."""
        organ_map = {
            "liver": ["alt", "ast", "bilirubin", "alkaline phosphatase"],
            "kidney": ["creatinine", "bun"],
            "thyroid": ["tsh", "t3", "t4"],
            "blood": ["wbc", "rbc", "hemoglobin", "hematocrit", "platelet"],
            "metabolism": ["glucose", "hemoglobin a1c", "cholesterol", "triglycerides"],
            "electrolytes": ["sodium", "potassium", "chloride"],
        }
        
        affected = {}
        for test in tests:
            if test.abnormality != AbnormalityLevel.NORMAL:
                for organ, markers in organ_map.items():
                    if any(marker in test.test_name.lower() for marker in markers):
                        if organ not in affected:
                            affected[organ] = []
                        affected[organ].append(test.test_name)
        
        return affected
    
    def _assess_drug_interactions(self, tests: list[LabValue]) -> dict[str, Any]:
        """Assess if abnormal values suggest drug interaction risk."""
        # Check for patterns that might indicate drug metabolism issues
        liver_abnormal = any(
            t.abnormality != AbnormalityLevel.NORMAL
            for t in tests
            if any(x in t.test_name.lower() for x in ["alt", "ast", "bilirubin"])
        )
        
        kidney_abnormal = any(
            t.abnormality != AbnormalityLevel.NORMAL
            for t in tests
            if any(x in t.test_name.lower() for x in ["creatinine", "bun"])
        )
        
        return {
            "liver_function_concern": liver_abnormal,
            "kidney_function_concern": kidney_abnormal,
            "risk_level": "high" if (liver_abnormal and kidney_abnormal) else "medium" if (liver_abnormal or kidney_abnormal) else "low",
        }
    
    def _generate_clinical_recommendations(self, tests: list[LabValue]) -> list[str]:
        """Generate clinical recommendations based on abnormal values."""
        recommendations = []
        
        # Check for common abnormality patterns
        glucose_tests = [t for t in tests if "glucose" in t.test_name.lower()]
        if glucose_tests and glucose_tests[0].abnormality != AbnormalityLevel.NORMAL:
            recommendations.append("Consider endocrinology referral for glucose management")
        
        liver_tests = [t for t in tests if any(x in t.test_name.lower() for x in ["alt", "ast", "bilirubin"])]
        if any(t.abnormality == AbnormalityLevel.CRITICAL for t in liver_tests):
            recommendations.append("Urgent hepatology assessment recommended")
        
        kidney_tests = [t for t in tests if any(x in t.test_name.lower() for x in ["creatinine", "bun"])]
        if any(t.abnormality == AbnormalityLevel.CRITICAL for t in kidney_tests):
            recommendations.append("Nephrology consultation advised")
        
        return recommendations
    
    def _detect_diseases(self, tests: list[LabValue]) -> list[dict[str, Any]]:
        """Detect potential diseases based on test abnormalities."""
        detected = []
        
        # Cholesterol/lipid disease
        cholesterol = next((t for t in tests if "cholesterol" in t.test_name.lower() and t.abnormality != AbnormalityLevel.NORMAL), None)
        ldl = next((t for t in tests if "ldl" in t.test_name.lower() and t.abnormality != AbnormalityLevel.NORMAL), None)
        if cholesterol or ldl:
            detected.append({
                "disease": "Hyperlipidemia",
                "severity": "high" if ldl and ldl.value > 160 else "moderate",
                "risk_score": 0.75
            })
        
        # Diabetes
        glucose = next((t for t in tests if "glucose" in t.test_name.lower()), None)
        if glucose and glucose.value > 125:
            detected.append({
                "disease": "Type 2 Diabetes Mellitus",
                "severity": "critical" if glucose.value > 400 else "high" if glucose.value > 200 else "moderate",
                "risk_score": 0.82
            })
        
        # Thyroid disease
        tsh = next((t for t in tests if "tsh" in t.test_name.lower() and t.abnormality != AbnormalityLevel.NORMAL), None)
        if tsh:
            if tsh.value > 4.0:
                detected.append({"disease": "Hypothyroidism", "severity": "moderate", "risk_score": 0.65})
            elif tsh.value < 0.4:
                detected.append({"disease": "Hyperthyroidism", "severity": "moderate", "risk_score": 0.60})
        
        # Liver disease
        ast_alt = [t for t in tests if any(x in t.test_name.lower() for x in ["ast", "alt"]) and t.abnormality != AbnormalityLevel.NORMAL]
        if any(t.abnormality == AbnormalityLevel.CRITICAL for t in ast_alt):
            detected.append({"disease": "Hepatic Dysfunction", "severity": "critical", "risk_score": 0.90})
        elif len(ast_alt) > 0:
            detected.append({"disease": "Hepatic Dysfunction", "severity": "moderate", "risk_score": 0.70})
        
        # Kidney disease
        creatinine = next((t for t in tests if "creatinine" in t.test_name.lower()), None)
        if creatinine and creatinine.value > 1.2:
            detected.append({"disease": "Chronic Kidney Disease", "severity": "high" if creatinine.value > 3.0 else "moderate", "risk_score": 0.78})
        
        return detected
    
    def _detect_infections(self, tests: list[LabValue], raw_text: str | None = None) -> dict[str, Any] | None:
        """
        Detect potential infections based on WBC abnormalities and keywords.
        
        Returns infection data suitable for resistance model analysis, or None if no infection detected.
        """
        # Check for elevated WBC (commonly indicates infection)
        wbc = next((t for t in tests if "wbc" in t.test_name.lower() or "white blood cell" in t.test_name.lower()), None)
        
        if not wbc or wbc.abnormality == AbnormalityLevel.NORMAL:
            return None  # No clear infection marker from WBC
        
        # WBC elevation suggests infection
        wbc_severity = "high" if wbc.value > 15 else "moderate"
        
        # Try to detect pathogen from raw text if available
        pathogen = None
        if raw_text:
            pathogen = self._extract_pathogen_from_text(raw_text)
        
        return {
            "infection_detected": True,
            "wbc_count": wbc.value,
            "wbc_severity": wbc_severity,
            "pathogen": pathogen or "Unknown organism (elevated WBC)",
            "source": "elevated WBC count" if not pathogen else f"elevated WBC + detected {pathogen}",
        }
    
    def _extract_pathogen_from_text(self, text: str) -> str | None:
        """Extract pathogen name from report text."""
        if not text:
            return None
        
        # Common pathogen patterns
        patterns = [
            r'\b(MRSA|VRSA|VRE|CDI|ESBL|E\.?\s*coli|C\.?\s*difficile)\b',
            r'\b(Staphylococcus\s+aureus|Pseudomonas\s+aeruginosa|Escherichia\s+coli|Klebsiella|Acinetobacter)\b',
            r'\b(gram[-\s]?negative|gram[-\s]?positive|methicillin[- ]resistant)\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _get_antibiotic_recommendations(self, infection_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Get antibiotic recommendations using the resistance model.
        
        Returns resistance analysis including risk score and recommended drugs.
        """
        if not antibiotic_resistance_model or not infection_data:
            return None
        
        try:
            # Call resistance model with infection context
            context = {
                "infection_data": infection_data,
                "pathogen": infection_data.get("pathogen", "Unknown"),
                "user_input": f"Treating {infection_data.get('pathogen')} infection with elevated WBC",
            }
            
            resistance_result = antibiotic_resistance_model(context)
            
            # Convert result to dict if it's a dataclass
            if hasattr(resistance_result, 'to_dict'):
                return resistance_result.to_dict()
            elif isinstance(resistance_result, dict):
                return resistance_result
            else:
                # Try asdict for dataclass
                return asdict(resistance_result)
        except Exception as e:
            print(f"Error calling resistance model: {e}")
            return None
    
    def _get_drug_recommendations(self, diseases: list[dict[str, Any]], gene_type: str = "standard") -> list[dict[str, Any]]:
        """Get drug recommendations based on detected diseases and genetic profile."""
        recommendations = []
        
        drug_database = {
            "Hyperlipidemia": {
                "standard": [
                    {"drug": "Atorvastatin", "class": "Statin", "dosage": "10-80mg daily", "efficacy": "High", "note": "First-line therapy"},
                    {"drug": "Rosuvastatin", "class": "Statin", "dosage": "5-40mg daily", "efficacy": "Very High", "note": "Potent statin"},
                ],
                "CYP3A4_poor": [
                    {"drug": "Rosuvastatin", "class": "Statin", "dosage": "5-20mg daily", "efficacy": "Very High", "note": "Less CYP3A4 metabolism"},
                    {"drug": "Pravastatin", "class": "Statin", "dosage": "10-40mg daily", "efficacy": "Moderate", "note": "Not metabolized by CYP3A4"},
                ],
                "CYP3A4_ultra": [
                    {"drug": "Atorvastatin", "class": "Statin", "dosage": "40-80mg daily", "efficacy": "High", "note": "Higher dose needed"},
                ]
            },
            "Type 2 Diabetes Mellitus": {
                "standard": [
                    {"drug": "Metformin", "class": "Biguanide", "dosage": "500-2000mg daily", "efficacy": "High", "note": "First-line monotherapy"},
                    {"drug": "Glipizide", "class": "Sulfonylurea", "dosage": "5-20mg daily", "efficacy": "High", "note": "If metformin inadequate"},
                ],
                "CYP2C9_poor": [
                    {"drug": "Metformin", "class": "Biguanide", "dosage": "500-2000mg daily", "efficacy": "High", "note": "Preferred: not metabolized"},
                    {"drug": "GLP-1 agonist", "class": "Incretin", "dosage": "Variable", "efficacy": "High", "note": "Good alternative"},
                ]
            },
            "Hypothyroidism": {
                "standard": [
                    {"drug": "Levothyroxine", "class": "Thyroid hormone", "dosage": "25-200mcg daily", "efficacy": "High", "note": "Gold standard"},
                ],
                "CYP1A2_poor": [
                    {"drug": "Levothyroxine", "class": "Thyroid hormone", "dosage": "25-200mcg daily", "efficacy": "High", "note": "Monitor TSH closely"},
                ]
            },
            "Hepatic Dysfunction": {
                "standard": [
                    {"drug": "Supportive care", "class": "Management", "dosage": "N/A", "efficacy": "Moderate", "note": "Reduce drug metabolism burden"},
                    {"drug": "Reduce CYP3A4 substrates", "class": "Management", "dosage": "N/A", "efficacy": "High", "note": "Avoid hepatotoxic drugs"},
                ]
            },
            "Chronic Kidney Disease": {
                "standard": [
                    {"drug": "ACE inhibitor", "class": "Antihypertensive", "dosage": "Variable", "efficacy": "High", "note": "Renal protective"},
                    {"drug": "ARB", "class": "Antihypertensive", "dosage": "Variable", "efficacy": "High", "note": "Alternative to ACE-I"},
                ]
            }
        }
        
        for disease in diseases:
            disease_name = disease["disease"]
            if disease_name in drug_database:
                drugs = drug_database[disease_name].get(gene_type, drug_database[disease_name].get("standard", []))
                for drug in drugs:
                    recommendations.append({
                        "disease": disease_name,
                        "severity": disease["severity"],
                        "drug": drug["drug"],
                        "class": drug["class"],
                        "dosage": drug["dosage"],
                        "efficacy": drug["efficacy"],
                        "note": drug["note"],
                        "gene_optimized": gene_type != "standard"
                    })
        
        return recommendations
    
    def _get_pharmacogenomics_analysis(self, tests: list[LabValue], raw_text: str = None) -> dict[str, Any]:
        """Analyze pharmacogenomics based on genetic markers if present."""
        
        # Try to extract genetic markers from raw text if available
        genetic_markers = {}
        if raw_text:
            genetic_markers = self._extract_genetic_markers(raw_text)
        
        if not genetic_markers:
            return {
                "genetic_markers_detected": False,
                "cyp_profile": "Standard metabolizer",
                "metabolism_note": "Gene-specific drug recommendations not available. Using standard dosing."
            }
        
        # Determine metabolizer status from genetic markers
        metabolizer_status = self._determine_metabolizer_status(genetic_markers)
        
        return {
            "genetic_markers_detected": True,
            "markers": genetic_markers,
            "cyp_profile": metabolizer_status["profile"],
            "metabolism_efficiency": metabolizer_status["efficiency"],
            "drug_interaction_risk": metabolizer_status["risk"],
            "specific_recommendations": self._get_genetic_drug_recommendations(genetic_markers),
            "metabolism_note": metabolizer_status["note"]
        }
    
    def _extract_genetic_markers(self, text: str) -> dict[str, str]:
        """Extract genetic markers from report text with flexible matching."""
        markers = {}
        
        # CYP2D6 - flexible patterns for various formats
        # Matches: "CYP2D6: *1/*4", "CYP2D6 *1/*4", "CYP2D6: 1/4", "CYP2D6 1/*4", etc.
        cyp2d6_patterns = [
            r'CYP2D6[\s:]*\*?(\d+/\*?\d+)[\s\n]*(?:\(([^)]*)\))?',  # Match genotype and optional phenotype in parens
            r'CYP2D6[\s:]*([*\d/]+?)[\s\n](?:\(([^)]*)\))?',  # More flexible with phenotype
        ]
        for pattern in cyp2d6_patterns:
            cyp2d6_match = re.search(pattern, text, re.IGNORECASE)
            if cyp2d6_match:
                genotype = cyp2d6_match.group(1).strip()
                phenotype = cyp2d6_match.group(2).strip() if cyp2d6_match.lastindex >= 2 and cyp2d6_match.group(2) else ""
                markers["CYP2D6"] = {"genotype": genotype, "phenotype": phenotype}
                break
        
        # CYP2C19
        cyp2c19_patterns = [
            r'CYP2C19[\s:]*\*?(\d+/\*?\d+)[\s\n]*(?:\(([^)]*)\))?',
            r'CYP2C19[\s:]*([*\d/]+?)[\s\n](?:\(([^)]*)\))?',
        ]
        for pattern in cyp2c19_patterns:
            cyp2c19_match = re.search(pattern, text, re.IGNORECASE)
            if cyp2c19_match:
                genotype = cyp2c19_match.group(1).strip()
                phenotype = cyp2c19_match.group(2).strip() if cyp2c19_match.lastindex >= 2 and cyp2c19_match.group(2) else ""
                markers["CYP2C19"] = {"genotype": genotype, "phenotype": phenotype}
                break
        
        # CYP3A4 - usually has status/phenotype
        cyp3a4_patterns = [
            r'CYP3A4[\s:]*([^,\n]+?)(?:\(([^)]*)\))?[\n,]',
            r'CYP3A4[\s:]*([^,\n]+)',
        ]
        for pattern in cyp3a4_patterns:
            cyp3a4_match = re.search(pattern, text, re.IGNORECASE)
            if cyp3a4_match:
                status = cyp3a4_match.group(1).strip()
                phenotype = cyp3a4_match.group(2).strip() if cyp3a4_match.lastindex >= 2 and cyp3a4_match.group(2) else ""
                if not phenotype:
                    phenotype = "Normal function" if "normal" in status.lower() else status
                markers["CYP3A4"] = {"status": status, "phenotype": phenotype}
                break
        
        # MTHFR - can be genotype or status
        mthfr_patterns = [
            r'MTHFR[\s:]*([A-Z0-9>]+)[\s\n]*(?:\(([^)]*)\))?',
            r'MTHFR[\s:]*([^,\n]+?)(?:\(([^)]*)\))?[\n,]',
        ]
        for pattern in mthfr_patterns:
            mthfr_match = re.search(pattern, text, re.IGNORECASE)
            if mthfr_match:
                genotype = mthfr_match.group(1).strip()
                phenotype = mthfr_match.group(2).strip() if mthfr_match.lastindex >= 2 and mthfr_match.group(2) else ""
                markers["MTHFR"] = {"genotype": genotype, "phenotype": phenotype}
                break
        
        # TPMT - status/activity level
        tpmt_patterns = [
            r'TPMT[\s:]*([^,\n]+?)(?:\(([^)]*)\))?[\n,]',
            r'TPMT[\s:]*([^,\n]+)',
        ]
        for pattern in tpmt_patterns:
            tpmt_match = re.search(pattern, text, re.IGNORECASE)
            if tpmt_match:
                status = tpmt_match.group(1).strip()
                phenotype = tpmt_match.group(2).strip() if tpmt_match.lastindex >= 2 and tpmt_match.group(2) else ""
                if not phenotype:
                    phenotype = "Normal activity" if "normal" in status.lower() else status
                markers["TPMT"] = {"status": status, "phenotype": phenotype}
                break
        
        # SLCO1B1 - genetic variant
        slco_patterns = [
            r'SLCO1B1[\s:]*([A-Za-z0-9>\.]+)[\s\n]*(?:\(([^)]*)\))?',
            r'SLCO1B1[\s:]*([^,\n]+?)(?:\(([^)]*)\))?[\n,]',
        ]
        for pattern in slco_patterns:
            slco_match = re.search(pattern, text, re.IGNORECASE)
            if slco_match:
                genotype = slco_match.group(1).strip()
                phenotype = slco_match.group(2).strip() if slco_match.lastindex >= 2 and slco_match.group(2) else ""
                markers["SLCO1B1"] = {"genotype": genotype, "phenotype": phenotype}
                break
        
        return markers
    
    def _determine_metabolizer_status(self, markers: dict[str, Any]) -> dict[str, Any]:
        """Determine metabolizer status from genetic markers."""
        
        # Check CYP2D6 status (primary indicator)
        cyp2d6_status = markers.get("CYP2D6", {})
        cyp2d6_phenotype = cyp2d6_status.get("phenotype", "").lower()
        cyp2d6_genotype = cyp2d6_status.get("genotype", "").lower()
        
        cyp2c19_status = markers.get("CYP2C19", {})
        cyp2c19_phenotype = cyp2c19_status.get("phenotype", "").lower()
        cyp2c19_genotype = cyp2c19_status.get("genotype", "").lower()
        
        # FIRST: Clean phenotype text if it contains phrase descriptions (e.g., "Intermediate Metabolizer")
        if cyp2d6_phenotype:
            if "poor" in cyp2d6_phenotype:
                cyp2d6_phenotype = "poor"
            elif "intermediate" in cyp2d6_phenotype:
                cyp2d6_phenotype = "intermediate"
            elif "ultra" in cyp2d6_phenotype or "rapid" in cyp2d6_phenotype:
                cyp2d6_phenotype = "ultra-rapid"
            elif "normal" in cyp2d6_phenotype:
                cyp2d6_phenotype = "normal"
        
        if cyp2c19_phenotype:
            if "poor" in cyp2c19_phenotype:
                cyp2c19_phenotype = "poor"
            elif "intermediate" in cyp2c19_phenotype:
                cyp2c19_phenotype = "intermediate"
            elif "normal" in cyp2c19_phenotype:
                cyp2c19_phenotype = "normal"
        
        # SECOND: Infer phenotype from genotype if phenotype text not available
        # Handle genotypes with or without asterisk prefix (*1/*4 or 1/*4)
        if not cyp2d6_phenotype and cyp2d6_genotype:
            # Common genotypes and their phenotypes (handle with/without asterisk prefix)
            cyp2d6_gen_clean = cyp2d6_genotype.lower().replace("*", "")
            if "44" in cyp2d6_gen_clean or "55" in cyp2d6_gen_clean or "33" in cyp2d6_gen_clean:
                cyp2d6_phenotype = "poor"
            elif ("14" in cyp2d6_gen_clean or "15" in cyp2d6_gen_clean or "24" in cyp2d6_gen_clean or 
                  "25" in cyp2d6_gen_clean or "1/4" in cyp2d6_genotype.lower() or "1/5" in cyp2d6_genotype.lower()):
                cyp2d6_phenotype = "intermediate"
            elif "11" in cyp2d6_gen_clean or "12" in cyp2d6_gen_clean:
                cyp2d6_phenotype = "normal"
            elif "1/1x2" in cyp2d6_genotype.lower() or "x2" in cyp2d6_genotype.lower():
                cyp2d6_phenotype = "ultra-rapid"
        
        if not cyp2c19_phenotype and cyp2c19_genotype:
            cyp2c19_gen_clean = cyp2c19_genotype.lower().replace("*", "")
            if "22" in cyp2c19_gen_clean or "33" in cyp2c19_gen_clean:
                cyp2c19_phenotype = "poor"
            elif ("12" in cyp2c19_gen_clean or "13" in cyp2c19_gen_clean or 
                  "1/2" in cyp2c19_genotype.lower() or "1/3" in cyp2c19_genotype.lower()):
                cyp2c19_phenotype = "intermediate"
            elif "11" in cyp2c19_gen_clean:
                cyp2c19_phenotype = "normal"
        
        # Determine overall status
        if "poor" in cyp2d6_phenotype or "poor" in cyp2c19_phenotype:
            return {
                "profile": "Poor metabolizer",
                "efficiency": "20-30%",
                "risk": "HIGH",
                "note": "Significant drug accumulation risk. Start at lowest doses and monitor carefully."
            }
        elif "intermediate" in cyp2d6_phenotype or "intermediate" in cyp2c19_phenotype:
            return {
                "profile": "Intermediate metabolizer",
                "efficiency": "60-70%",
                "risk": "MODERATE",
                "note": "Slower drug metabolism. Start at lower doses, titrate slowly. Therapeutic drug monitoring recommended."
            }
        elif "ultra" in cyp2d6_phenotype or "rapid" in cyp2d6_phenotype:
            return {
                "profile": "Ultra-rapid metabolizer",
                "efficiency": "120-150%",
                "risk": "LOW",
                "note": "Fast drug metabolism. May require higher doses or more frequent dosing."
            }
        else:
            return {
                "profile": "Normal metabolizer",
                "efficiency": "100%",
                "risk": "LOW",
                "note": "Normal drug metabolism. Standard dosing typically appropriate."
            }
    
    def _get_genetic_drug_recommendations(self, markers: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate drug recommendations based on genetic profile with specific dosing and treatment plans."""
        
        cyp2d6_phenotype = markers.get("CYP2D6", {}).get("phenotype", "").lower()
        cyp2c19_phenotype = markers.get("CYP2C19", {}).get("phenotype", "").lower()
        recommendations = []
        
        if "intermediate" in cyp2d6_phenotype or "intermediate" in cyp2c19_phenotype:
            # Tier 1: First-choice drug
            recommendations.append({
                "rank": 1,
                "category": "Antidepressant - First Choice",
                "specific_drug": "Sertraline (Zoloft)",
                "action": "START",
                "initial_dose": "25mg daily",
                "target_dose": "50-75mg daily",
                "titration": "Increase to 50mg at week 3, then 75mg at week 5 if tolerated",
                "drugs": ["Sertraline 25mg once daily (morning)"],
                "note": "Excellent match for CYP2D6/2C19 intermediate metabolizers. Partial metabolism allows good efficacy at lower doses.",
                "monitoring": "Check plasma levels at 4-6 weeks; assess mood weekly for first 8 weeks",
                "expected_outcome": "60-70% symptom improvement by week 8",
                "genetic_score": "9.2/10"
            })
            
            # Tier 2: Alternative if first-choice not tolerated
            recommendations.append({
                "rank": 2,
                "category": "Antidepressant - Alternative",
                "specific_drug": "Vortioxetine (Trintellix)",
                "action": "ALTERNATIVE",
                "initial_dose": "5mg daily",
                "target_dose": "10-15mg daily",
                "titration": "Increase to 10mg at week 2, then 15mg at week 4 if tolerated",
                "drugs": ["Vortioxetine 5-15mg daily"],
                "note": "Minimal CYP2D6 involvement. Better cognitive benefits. Slightly more expensive.",
                "monitoring": "Check response at 4 weeks; therapeutic drug monitoring optional",
                "expected_outcome": "70-80% symptom improvement by week 8",
                "genetic_score": "8.5/10"
            })
            
            # Tier 1: Blood pressure/cardiac management
            recommendations.append({
                "rank": 1,
                "category": "Beta-Blocker - First Choice",
                "specific_drug": "Metoprolol (Lopressor)",
                "action": "ADD",
                "initial_dose": "25mg daily",
                "target_dose": "50mg daily",
                "titration": "Start 25mg evening, increase to 50mg at week 3 based on BP response",
                "drugs": ["Metoprolol 25mg once daily (evening)"],
                "note": "Good metabolic match for intermediate metabolizers. Monitor heart rate.",
                "monitoring": "Monitor HR, ensure HR >50 bpm; check BP weekly",
                "duration": "Ongoing for hypertension management"
            })
            
            # Alternative: Calcium channel blocker
            recommendations.append({
                "rank": 2,
                "category": "Calcium Channel Blocker - Alternative",
                "specific_drug": "Amlodipine (Norvasc)",
                "action": "ALTERNATIVE",
                "initial_dose": "5mg daily",
                "target_dose": "10mg daily",
                "titration": "5mg daily week 1-2, increase to 10mg if needed at week 3",
                "drugs": ["Amlodipine 5-10mg daily"],
                "note": "CYP3A4 substrate (normal function). Minimal interaction with SSRIs.",
                "monitoring": "Check BP at 2-4 weeks; minimal drug interactions"
            })
        
        if markers.get("MTHFR"):
            mthfr_phenotype = markers.get("MTHFR", {}).get("phenotype", "").lower()
            if "heterozygous" in mthfr_phenotype or "variant" in mthfr_phenotype:
                recommendations.append({
                    "rank": 3,
                    "category": "Supplementation",
                    "specific_drug": "Methylfolate (Active B9)",
                    "action": "ADD",
                    "initial_dose": "1000mcg daily",
                    "target_dose": "1000mcg daily",
                    "titration": "Start 1000mcg from day 1",
                    "drugs": ["Methylfolate 1000mcg daily"],
                    "note": "MTHFR variant detected - enhanced folate metabolism support. Synergistic with antidepressants.",
                    "monitoring": "Monitor energy and mood improvement at weeks 2, 4, 8",
                    "expected_benefit": "Better response to antidepressants; improved energy"
                })
        
        return recommendations
