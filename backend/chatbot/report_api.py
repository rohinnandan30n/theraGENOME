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
    import fitz  # PyMuPDF for PDF handling
    
    from backend.chatbot.report_analyzer import ReportAnalyzer, ParsedReport
    from backend.chatbot.mode_filter import ModeFilter
    
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


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
            if not request.text.strip():
                raise ValueError("Please provide some report text to analyze")
            
            # Parse report from pasted text
            parsed_report = _analyzer.parse(
                extracted_text=request.text,
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
