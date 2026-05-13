import io
import unittest
from unittest.mock import MagicMock
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.chatbot.report_api import DocumentExtractor

class TestDocxExtraction(unittest.TestCase):
    def test_extract_from_docx_basic(self):
        # Mock docx library since it might not be installed in the environment
        # but we want to test the logic if it were
        try:
            import docx
            HAS_DOCX = True
        except ImportError:
            HAS_DOCX = False
            print("python-docx not installed, skipping real extraction test")
            return

        # Create a simple docx in memory for testing
        doc = docx.Document()
        doc.add_paragraph("Patient: Jane Doe")
        doc.add_paragraph("HEMOGLOBIN: 14.5 g/dL")
        
        table = doc.add_table(rows=2, cols=2)
        table.rows[0].cells[0].text = "Test"
        table.rows[0].cells[1].text = "Value"
        table.rows[1].cells[0].text = "GLUCOSE"
        table.rows[1].cells[1].text = "110"
        
        docx_bytes = io.BytesIO()
        doc.save(docx_bytes)
        docx_content = docx_bytes.getvalue()
        
        extractor = DocumentExtractor()
        text = extractor.extract_from_docx(docx_content)
        
        self.assertIn("Patient: Jane Doe", text)
        self.assertIn("HEMOGLOBIN: 14.5 g/dL", text)
        self.assertIn("GLUCOSE | 110", text)
        print("Success: Docx extraction verified!")

if __name__ == "__main__":
    unittest.main()
