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
            raw_text=extracted_text[:500] if extracted_text else None,
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
        
        Includes: statistics, abnormality patterns, correlations, recommendations
        """
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
            "organ_involvement": self._correlate_to_organs(report.tests),
            "drug_interaction_risk": self._assess_drug_interactions(report.tests),
            "recommendations": self._generate_clinical_recommendations(report.tests),
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
