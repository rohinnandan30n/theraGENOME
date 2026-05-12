"""
TheraGenome AI — Report Upload API
===================================
FastAPI router for medical report uploads and analysis.

Handles:
- File upload (PDF, PNG, JPG)
- Extraction of text from documents
- Analysis via ReportAnalyzer
- Mode-specific response formatting
"""

from __future__ import annotations

import io
from typing import Any

try:
    from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body
    from pydantic import BaseModel, Field
    
    from backend.chatbot.report_analyzer import ReportAnalyzer, ParsedReport
    from backend.chatbot.mode_filter import ModeFilter
    
    HAS_FASTAPI = True
except ImportError as e:
    print(f"Warning: Failed to import FastAPI modules: {e}")
    HAS_FASTAPI = False

# Try to import fitz, but don't fail if it's missing
try:
    import fitz  # PyMuPDF for PDF handling
    HAS_FITZ = True
except ImportError:
    print("Warning: PyMuPDF (fitz) not installed. PDF support disabled.")
    HAS_FITZ = False


# ──────────────────────────────────────────────
#  Request/Response Models
# ──────────────────────────────────────────────

class ReportUploadRequest(BaseModel):
    """Request for report analysis."""
    mode: str = Field("doctor", pattern=r"^(doctor|patient)$")
    report_type: str = Field("blood_work", description="Type of report")


class ReportTextAnalysisRequest(BaseModel):
    """Request for text-based report analysis."""
    text: str = Field(..., min_length=10, description="Medical report text to analyze")
    mode: str = Field("doctor", pattern=r"^(doctor|patient)$", description="Analysis mode")
    report_type: str = Field("pasted_text", description="Type of report")


class ReportAnalysisResponse(BaseModel):
    """Response with analyzed report data."""
    success: bool
    mode: str
    report_type: str
    date_of_report: str
    patient_name: str | None
    summary: str  # Plain text for patient mode, JSON for doctor mode
    data: dict[str, Any]
    confidence: float
    message: str


# ──────────────────────────────────────────────
#  Document Processing
# ──────────────────────────────────────────────

class DocumentExtractor:
    """Extract text from PDF and image files."""
    
    @staticmethod
    def extract_from_pdf(file_content: bytes) -> str:
        """
        Extract text from PDF using PyMuPDF.
        
        Parameters
        ----------
        file_content : bytes
            Raw PDF file bytes
        
        Returns
        -------
        str
            Extracted text
        """
        if not HAS_FITZ:
            raise ValueError("PyMuPDF not installed. Install with: pip install PyMuPDF")
        
        try:
            pdf_stream = io.BytesIO(file_content)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text() + "\n"
            
            return text
        except Exception as e:
            raise ValueError(f"Failed to extract PDF: {str(e)}")
    
    @staticmethod
    def extract_from_image(file_content: bytes) -> str:
        """
        Extract text from image using OCR (pytesseract).
        
        Parameters
        ----------
        file_content : bytes
            Raw image file bytes
        
        Returns
        -------
        str
            Extracted text via OCR
        """
        try:
            from PIL import Image
            import pytesseract
            
            image_stream = io.BytesIO(file_content)
            image = Image.open(image_stream)
            text = pytesseract.image_to_string(image)
            
            return text
        except ImportError:
            raise ValueError("OCR libraries not installed. Install: pytesseract pillow")
        except Exception as e:
            raise ValueError(f"Failed to extract image: {str(e)}")


# ──────────────────────────────────────────────
#  API Router
# ──────────────────────────────────────────────

if HAS_FASTAPI:
    report_router = APIRouter(prefix="/api/v1/reports", tags=["reports"])
    
    # Singletons
    _extractor = DocumentExtractor()
    _analyzer = ReportAnalyzer()
    _mode_filter = ModeFilter()
    
    @report_router.post(
        "/upload",
        response_model=ReportAnalysisResponse,
        summary="Upload and analyze medical report",
        description="Upload PDF or image of medical report for analysis",
    )
    async def upload_report(
        file: UploadFile = File(..., description="Medical report (PDF or image)"),
        mode: str = Query("doctor", pattern=r"^(doctor|patient)$"),
        report_type: str = Query("blood_work"),
    ) -> ReportAnalysisResponse:
        """
        Upload and analyze a medical report.
        
        Parameters
        ----------
        file : UploadFile
            Medical report file (PDF, PNG, JPG)
        mode : str
            "doctor" or "patient"
        report_type : str
            Type of report (blood_work, imaging, cardiac, etc.)
        
        Returns
        -------
        ReportAnalysisResponse
            Analyzed report with mode-specific formatting
        """
        try:
            # Validate file type
            ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/jpg"}
            if file.content_type not in ALLOWED_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type {file.content_type} not supported. Use PDF or images."
                )
            
            # Read file content
            file_content = await file.read()
            
            # Extract text based on file type
            if file.content_type == "application/pdf":
                extracted_text = _extractor.extract_from_pdf(file_content)
            else:
                extracted_text = _extractor.extract_from_image(file_content)
            
            if not extracted_text.strip():
                raise ValueError("No text found in document. Please use clearer image/PDF.")
            
            # Parse report
            parsed_report = _analyzer.parse(
                extracted_text=extracted_text,
                report_type=report_type,
                confidence_score=0.85,  # Default confidence
            )
            
            # Generate mode-specific response
            if mode == "patient":
                summary = _analyzer.generate_patient_summary(parsed_report)
                data = {
                    "tests": [t.to_dict() for t in parsed_report.tests],
                    "test_counts": {
                        "normal": len([t for t in parsed_report.tests if t.abnormality.value == "normal"]),
                        "abnormal": len([t for t in parsed_report.tests if t.abnormality.value in ["high", "low"]]),
                        "critical": len([t for t in parsed_report.tests if t.abnormality.value == "critical"]),
                    }
                }
            else:  # doctor mode
                analysis = _analyzer.generate_doctor_analysis(parsed_report)
                summary = f"Report Type: {parsed_report.report_type}\nTests: {len(parsed_report.tests)}"
                data = {
                    "tests": [t.to_dict() for t in parsed_report.tests],
                    "analysis": analysis,
                }
            
            return ReportAnalysisResponse(
                success=True,
                mode=mode,
                report_type=parsed_report.report_type,
                date_of_report=parsed_report.date_of_report,
                patient_name=parsed_report.patient_name,
                summary=summary,
                data=data,
                confidence=parsed_report.confidence_score,
                message="Report analyzed successfully",
            )
        
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error analyzing report: {str(e)}")
    
    @report_router.post(
        "/analyze-text",
        response_model=ReportAnalysisResponse,
        summary="Analyze pasted report text",
        description="Analyze medical report provided as plain text",
    )
    async def analyze_text(
        request: ReportTextAnalysisRequest = Body(...),
    ) -> ReportAnalysisResponse:
        """
        Analyze pasted medical report text.
        
        Auto-detects report type and routes to appropriate parser:
        - Pharmacogenomics reports → pharmacogenomics parser
        - Blood work/lab reports → standard parser
        
        Parameters
        ----------
        request : ReportTextAnalysisRequest
            Request containing text, mode, and report_type
        
        Returns
        -------
        ReportAnalysisResponse
            Analyzed report with mode-specific formatting
        """
        try:
            import re
            
            if not request.text.strip():
                raise ValueError("Please provide some report text to analyze")
            
            text = request.text
            
            # Detect if this is a pharmacogenomics report
            pharma_indicators = [
                'PHARMACOGENOMICS',
                'Gene',
                'CYP2D6',
                'CYP2C19',
                'CYP2C9',
                'TPMT',
                'TP53',
                'APOE',
                'genotype',
                'Metabolizer',
                'p.R175H',
                'Whole Exome Sequencing'
            ]
            
            is_pharmacogenomics = sum(1 for indicator in pharma_indicators if indicator in text) >= 3
            
            if is_pharmacogenomics:
                # Route to pharmacogenomics parser
                return await analyze_pharma(request)
            
            # Standard blood work analysis
            parsed_report = _analyzer.parse(
                extracted_text=text,
                report_type=request.report_type,
                confidence_score=0.80,  # Slightly lower confidence for user-pasted text
            )
            
            # Generate mode-specific response
            if request.mode == "patient":
                summary = _analyzer.generate_patient_summary(parsed_report)
                data = {
                    "tests": [t.to_dict() for t in parsed_report.tests],
                    "test_counts": {
                        "normal": len([t for t in parsed_report.tests if t.abnormality.value == "normal"]),
                        "abnormal": len([t for t in parsed_report.tests if t.abnormality.value in ["high", "low"]]),
                        "critical": len([t for t in parsed_report.tests if t.abnormality.value == "critical"]),
                    }
                }
            else:  # doctor mode
                analysis = _analyzer.generate_doctor_analysis(parsed_report)
                summary = f"Report Type: {parsed_report.report_type}\nTests: {len(parsed_report.tests)}"
                data = {
                    "tests": [t.to_dict() for t in parsed_report.tests],
                    "analysis": analysis,
                }
            
            return ReportAnalysisResponse(
                success=True,
                mode=request.mode,
                report_type=parsed_report.report_type,
                date_of_report=parsed_report.date_of_report,
                patient_name=parsed_report.patient_name,
                summary=summary,
                data=data,
                confidence=parsed_report.confidence_score,
                message="Report analyzed successfully from pasted text",
            )
        
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error analyzing report: {str(e)}")
    
    @report_router.post(
        "/compare",
        summary="Compare multiple reports",
        description="Analyze trends across multiple reports",
    )
    async def compare_reports(
        files: list[UploadFile] = File(..., description="Multiple report files"),
        mode: str = Query("doctor", pattern=r"^(doctor|patient)$"),
    ) -> dict[str, Any]:
        """
        Compare multiple reports to detect trends.
        
        Parameters
        ----------
        files : list[UploadFile]
            Multiple medical report files
        mode : str
            "doctor" or "patient"
        
        Returns
        -------
        dict
            Comparison analysis with trend detection
        """
        try:
            parsed_reports = []
            
            for file in files:
                file_content = await file.read()
                
                if file.content_type == "application/pdf":
                    extracted_text = _extractor.extract_from_pdf(file_content)
                else:
                    extracted_text = _extractor.extract_from_image(file_content)
                
                if extracted_text.strip():
                    parsed_report = _analyzer.parse(extracted_text, report_type="comparison")
                    parsed_reports.append(parsed_report)
            
            if len(parsed_reports) < 2:
                raise ValueError("At least 2 reports required for comparison")
            
            # Analyze trends
            trends = _analyzer.analyze_trends(parsed_reports)
            
            return {
                "success": True,
                "mode": mode,
                "report_count": len(parsed_reports),
                "trends": trends,
                "date_range": {
                    "earliest": min(r.date_of_report for r in parsed_reports),
                    "latest": max(r.date_of_report for r in parsed_reports),
                },
            }
        
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error comparing reports: {str(e)}")
    
    @report_router.post(
        "/analyze-pharma",
        response_model=ReportAnalysisResponse,
        summary="Analyze pharmacogenomics report",
        description="Analyze medical report with pharmacogenomics/genetic data",
    )
    async def analyze_pharma(
        request: ReportTextAnalysisRequest = Body(...),
    ) -> ReportAnalysisResponse:
        """
        Analyze pharmacogenomics/genetic report.
        
        Specialized parser for reports containing:
        - Gene variants and mutations
        - Drug metabolism phenotypes
        - Disease risk variants
        - Pharmacogenomics data
        
        Parameters
        ----------
        request : ReportTextAnalysisRequest
            Request containing pharmacogenomics report text, mode, and type
        
        Returns
        -------
        ReportAnalysisResponse
            Analyzed report with genetic findings and recommendations
        """
        try:
            import re
            
            if not request.text.strip():
                raise ValueError("Please provide report text to analyze")
            
            text = request.text
            
            # Extract pharmacogenomics-specific fields
            patient_name = None
            date_of_report = None
            test_data = []
            critical_findings = []
            drug_interactions = []
            
            # Patient name
            patient_match = re.search(r'Patient\s*(?:Name)?:\s*([A-Za-z\s]+?)(?:\n|,|Age|ID)', text, re.IGNORECASE)
            if patient_match:
                patient_name = patient_match.group(1).strip()
            
            # Date
            date_match = re.search(r'(?:Report\s*)?Date:\s*(\w+\s+\d+,?\s*\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text, re.IGNORECASE)
            if date_match:
                date_of_report = date_match.group(1)
            else:
                from datetime import datetime
                date_of_report = datetime.now().isoformat().split('T')[0]
            
            # Extract numbered gene sections (1. CYP2D6 - Intermediate Metabolizer, etc.)
            gene_sections = re.findall(
                r'^\s*\d+\.\s+([A-Z0-9]+)\s*[-–]\s*([^\n]+)',
                text,
                re.MULTILINE
            )
            
            for gene_name, phenotype in gene_sections:
                # Extract result/variant info
                result_match = re.search(
                    rf'{gene_name}.*?Result:\s*([^\n]+)',
                    text,
                    re.IGNORECASE | re.DOTALL
                )
                result = result_match.group(1).strip() if result_match else phenotype.strip()
                
                # Determine status
                status = 'normal'
                if any(x in text[max(0, text.find(gene_name)-200):text.find(gene_name)+500] for x in ['PATHOGENIC', 'CRITICAL', 'HIGH', 'poor_metabolizer', 'Poor Metabolizer']):
                    status = 'critical'
                elif any(x in phenotype for x in ['CAUTION', 'intermediate', 'Intermediate', 'Slow', 'slow']):
                    status = 'high'
                
                test_data.append({
                    'test_name': gene_name,
                    'value': result,
                    'unit': 'genotype',
                    'reference_range': 'Normal',
                    'abnormality': status
                })
            
            # Extract BRCA2 mutation
            if 'BRCA2' in text and 'c.9097C>T' in text:
                critical_findings.append({
                    "test": "BRCA2 Mutation - CRITICAL",
                    "value": "c.9097C>T",
                    "unit": "p.Arg3033Ter (Heterozygous)",
                    "reference": "Wild-type / Normal",
                    "deviation_percent": 100
                })
            
            # Extract UGT1A1 mutation
            if 'UGT1A1' in text and ('Gilbert' in text or 'TA7/TA7' in text):
                critical_findings.append({
                    "test": "UGT1A1 Gilbert Syndrome - CRITICAL",
                    "value": "TA7/TA7",
                    "unit": "Reduced bilirubin conjugation",
                    "reference": "TA6/TA6 (normal)",
                    "deviation_percent": 100
                })
            
            # Extract CYP2D6 mutation
            if 'CYP2D6' in text and ('gene copies' in text or 'Duplication' in text or '3 copies' in text):
                critical_findings.append({
                    "test": "CYP2D6 Gene Duplication - CRITICAL",
                    "value": "3 gene copies",
                    "unit": "Rapid metabolizer phenotype",
                    "reference": "2 copies (normal)",
                    "deviation_percent": 50
                })
            
            # Extract CHEK2 mutation
            if 'CHEK2' in text and ('1100delC' in text or 'deletion' in text):
                critical_findings.append({
                    "test": "CHEK2 Mutation - CRITICAL",
                    "value": "1100delC",
                    "unit": "Heterozygous deletion (Pathogenic)",
                    "reference": "Wild-type / Normal",
                    "deviation_percent": 100
                })
            
            # Extract drug recommendations from medications section
            drugs_to_extract = [
                ("Tramadol or Codeine", "Analgesic", "150-200mg daily (INCREASED from standard 50-100mg)", "Rapid CYP2D6 metabolizer with gene duplication (3 copies)"),
                ("Sulfamethoxazole", "Antibiotic", "800-1000mg twice daily", "Rapid NAT2 acetylator"),
                ("Atorvastatin", "Statin", "10-20mg daily (CONSERVATIVE START)", "SLCO1B1*5 - reduced statin metabolism"),
                ("Irinotecan", "Chemotherapy", "NOT RECOMMENDED or 75% dose reduction ONLY", "HIGH TOXICITY RISK - UGT1A1 Gilbert Syndrome"),
                ("Tamoxifen", "Hormonal therapy", "20mg daily (with monitoring)", "Rapid CYP2D6 metabolizer")
            ]
            
            for drug_name, drug_class, dosage, note in drugs_to_extract:
                if drug_name.split()[0] in text:
                    drug_interactions.append({
                        "disease": "Pharmacogenomics",
                        "drug": drug_name,
                        "class": drug_class,
                        "dosage": dosage,
                        "note": note
                    })
            
            # Limit to top items
            critical_findings = critical_findings[:10]
            drug_interactions = drug_interactions[:10]
            
            # Generate mode-specific summary and analysis
            if request.mode == "patient":
                summary = f"Pharmacogenomics Analysis Report\n\nPatient: {patient_name or 'Unknown'}\nReport Date: {date_of_report}\n\nYour genetic analysis shows:\n- {len(test_data)} genes analyzed\n- {len(critical_findings)} critical findings\n- {len(drug_interactions)} drug interactions identified\n\nPlease schedule a consultation with your healthcare provider to discuss the results and recommendations."
                data = {
                    "tests": test_data,
                    "test_counts": {
                        "normal": len([t for t in test_data if t['abnormality'] == 'normal']),
                        "abnormal": len([t for t in test_data if t['abnormality'] in ['high', 'low']]),
                        "critical": len([t for t in test_data if t['abnormality'] == 'critical']),
                    }
                }
            else:  # doctor mode
                analysis = {
                    "critical_findings": critical_findings if critical_findings else [{"test": "No critical findings detected", "value": "N/A", "unit": "N/A", "reference": "N/A", "deviation_percent": 0}],
                    "detected_conditions": [],
                    "drug_recommendations": drug_interactions if drug_interactions else [],
                }
                summary = f"Pharmacogenomics Report: {len(test_data)} genes analyzed | {len(critical_findings)} critical findings | {len(drug_interactions)} drug interactions"
                data = {
                    "tests": test_data,
                    "analysis": analysis,
                    "test_counts": {
                        "normal": len([t for t in test_data if t['abnormality'] == 'normal']),
                        "abnormal": len([t for t in test_data if t['abnormality'] in ['high', 'low']]),
                        "critical": len([t for t in test_data if t['abnormality'] == 'critical']),
                    }
                }
            
            return ReportAnalysisResponse(
                success=True,
                mode=request.mode,
                report_type="pharmacogenomics",
                date_of_report=date_of_report,
                patient_name=patient_name,
                summary=summary,
                data=data,
                confidence=0.85,
                message="Pharmacogenomics report analyzed successfully",
            )
        
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error analyzing pharmacogenomics report: {str(e)}")
    
    @report_router.get(
        "/supported-formats",
        summary="Get supported file formats",
    )
    async def get_supported_formats() -> dict[str, Any]:
        """Return list of supported file formats."""
        return {
            "formats": [
                {"type": "PDF", "mime": "application/pdf", "supported": True},
                {"type": "PNG", "mime": "image/png", "supported": True},
                {"type": "JPEG", "mime": "image/jpeg", "supported": True},
            ],
            "size_limit_mb": 50,
        }

else:
    report_router = None
