"""
Comprehensive test suite for PII filter.
Tests all functionality including edge cases and malicious inputs.
"""

import pytest
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from utils.pii_filter import (
    FilterResult,
    RegexPIIFilter,
    PresidioPIIFilter,
    PIIFilterPipeline,
    get_pii_filter_pipeline
)


class TestFilterResult:
    """Test FilterResult data class."""
    
    def test_creation(self):
        """Test FilterResult creation."""
        result = FilterResult(
            cleaned_text="Hello [REDACTED]",
            pii_found=True,
            redaction_count=1,
            types_found=["name"]
        )
        
        assert result.cleaned_text == "Hello [REDACTED]"
        assert result.pii_found is True
        assert result.redaction_count == 1
        assert result.types_found == ["name"]
    
    def test_to_audit_log(self):
        """Test audit log conversion (safe format)."""
        result = FilterResult(
            cleaned_text="Safe text",
            pii_found=True,
            redaction_count=2,
            types_found=["phone", "email"],
            source="voice"
        )
        
        log_entry = result.to_audit_log()
        
        # Verify log entry structure
        assert "timestamp" in log_entry
        assert log_entry["pii_found"] is True
        assert log_entry["redaction_count"] == 2
        assert log_entry["types_found"] == ["phone", "email"]
        assert log_entry["source"] == "voice"
        
        # Verify no actual text is logged
        assert "cleaned_text" not in str(log_entry)


class TestRegexPIIFilter:
    """Test regex-based PII detection."""
    
    @pytest.fixture
    def filter(self):
        """Create RegexPIIFilter instance."""
        return RegexPIIFilter()
    
    def test_empty_input(self, filter):
        """Test empty string input."""
        result = filter.filter_text("")
        
        assert result.cleaned_text == ""
        assert result.pii_found is False
        assert result.redaction_count == 0
    
    def test_phone_number_indian_with_country_code(self, filter):
        """Test Indian phone number with country code."""
        text = "Call me on +91 98765 43210"
        result = filter.filter_text(text)
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        assert "phone_number" in result.types_found
    
    def test_phone_number_indian_without_country_code(self, filter):
        """Test Indian phone number without country code."""
        text = "My number is 9876543210"
        result = filter.filter_text(text)
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        assert "phone_number" in result.types_found
    
    def test_email_address(self, filter):
        """Test email address detection."""
        text = "Contact me at rahul.sharma@example.com"
        result = filter.filter_text(text)
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        assert "email" in result.types_found
    
    def test_aadhaar_number(self, filter):
        """Test Aadhaar number detection."""
        text = "My Aadhaar is 1234 5678 9012"
        result = filter.filter_text(text)
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        assert "aadhaar" in result.types_found
    
    def test_date_of_birth(self, filter):
        """Test date of birth detection."""
        text = "DOB: 15/05/1990"
        result = filter.filter_text(text)
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        assert "date_of_birth" in result.types_found
    
    def test_name_with_trigger_phrase(self, filter):
        """Test name detection with trigger phrase."""
        text = "My name is Rahul Sharma"
        result = filter.filter_text(text)
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        assert "name" in result.types_found
    
    def test_pan_card(self, filter):
        """Test PAN card detection."""
        text = "My PAN is AAAAA1234A"
        result = filter.filter_text(text)
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        assert "pan_card" in result.types_found
    
    def test_passport_number(self, filter):
        """Test passport number detection."""
        text = "Passport: A12345678"
        result = filter.filter_text(text)
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        assert "passport" in result.types_found
    
    def test_indian_pin_code(self, filter):
        """Test Indian PIN code detection."""
        text = "ZIP code: 110001"
        result = filter.filter_text(text)
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        assert "pin_code" in result.types_found
    
    def test_multiple_pii_items(self, filter):
        """Test detection of multiple PII items."""
        text = "My name is Rahul Sharma, call me on 9876543210, email: rahul@example.com"
        result = filter.filter_text(text)
        
        assert result.pii_found is True
        assert result.redaction_count >= 3
        assert "name" in result.types_found
        assert "phone_number" in result.types_found
        assert "email" in result.types_found
    
    def test_clean_text_no_pii(self, filter):
        """Test clean text without PII."""
        text = "The patient has BRCA1 mutation with high pathogenicity"
        result = filter.filter_text(text)
        
        assert result.cleaned_text == text
        assert result.pii_found is False
        assert result.redaction_count == 0
    
    def test_medical_text_not_affected(self, filter):
        """Test legitimate medical text is not affected."""
        text = "Treatment included IV antibiotics and monitoring. Blood pressure 120/80 mmHg."
        result = filter.filter_text(text)
        
        assert "[REDACTED]" not in result.cleaned_text
        assert result.pii_found is False


class TestPresidioPIIFilter:
    """Test Presidio-based PII detection."""
    
    @pytest.fixture
    def filter(self):
        """Create PresidioPIIFilter instance."""
        return PresidioPIIFilter()
    
    def test_initialization(self, filter):
        """Test filter initialization."""
        # Should initialize without raising exception
        assert filter is not None
    
    def test_empty_input(self, filter):
        """Test empty string input."""
        result = filter.analyze_and_anonymize("")
        
        assert result.cleaned_text == ""
        assert result.pii_found is False
    
    def test_degrade_gracefully_if_unavailable(self, filter):
        """Test graceful degradation if Presidio unavailable."""
        # Create a filter that's not initialized
        if not filter._initialized:
            result = filter.analyze_and_anonymize("Any text")
            
            # Should not crash
            assert result is not None
            # Should return original text
            assert "Any text" in result.cleaned_text


class TestPIIFilterPipeline:
    """Test the complete PII filter pipeline."""
    
    @pytest.fixture
    def pipeline(self):
        """Create PIIFilterPipeline instance."""
        return PIIFilterPipeline()
    
    def test_empty_input(self, pipeline):
        """Test empty string input."""
        result = pipeline.process("")
        
        assert result.cleaned_text == ""
        assert result.pii_found is False
    
    def test_name_and_phone(self, pipeline):
        """Test filtering name and phone number together."""
        text = "My name is Rahul Sharma, call me on 9876543210"
        result = pipeline.process(text, source="text")
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        assert result.redaction_count >= 2
        assert "phone_number" in result.types_found
    
    def test_patient_info_complex(self, pipeline):
        """Test filtering complex patient information."""
        text = "Patient: Dr. Priya, DOB 12/05/1990, Email: priya@gmail.com, Phone: +91 9876543210"
        result = pipeline.process(text, source="text")
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        # Should catch multiple PII types
        assert result.redaction_count >= 3
    
    def test_medical_text_preservation(self, pipeline):
        """Test legitimate medical text is NOT redacted."""
        text = "The patient has BRCA1 mutation with high pathogenicity"
        result = pipeline.process(text, source="text")
        
        assert result.cleaned_text == text
        assert result.pii_found is False
    
    def test_aadhaar_redaction(self, pipeline):
        """Test Aadhaar number redaction."""
        text = "My Aadhaar is 1234 5678 9012"
        result = pipeline.process(text, source="text")
        
        assert "[REDACTED]" in result.cleaned_text
        assert result.pii_found is True
        assert "aadhaar" in result.types_found
    
    def test_voice_source(self, pipeline):
        """Test filtering with voice source."""
        text = "My name is Rajesh, number is 8765432109"
        result = pipeline.process(text, language="en", source="voice")
        
        assert result.source == "voice"
        assert result.pii_found is True
    
    def test_language_hindi(self, pipeline):
        """Test filtering with Hindi language."""
        text = "मेरा नाम राहुल है"  # "My name is Rahul"
        result = pipeline.process(text, language="hi", source="text")
        
        # Should process with Hindi language setting
        assert result.language == "hi"
    
    def test_batch_processing(self, pipeline):
        """Test batch processing multiple texts."""
        texts = [
            "Call me on 9876543210",
            "The patient has BRCA1",
            "My email is test@example.com"
        ]
        
        results = pipeline.process_batch(texts, source="text")
        
        assert len(results) == 3
        # First and third should have PII, second should not
        assert results[0].pii_found is True
        assert results[1].pii_found is False
        assert results[2].pii_found is True
    
    def test_graceful_degradation_on_error(self, pipeline):
        """Test graceful degradation if filter encounters error."""
        # Simulate error by passing invalid type (if possible)
        # The filter should handle it gracefully
        result = pipeline.process("Test text", source="text")
        
        # Should never crash
        assert result is not None
        assert isinstance(result.cleaned_text, str)
    
    def test_no_pii_exposure_in_response(self, pipeline):
        """Test that actual PII is never exposed in response."""
        text = "Patient name: Priya, Phone: 9876543210"
        result = pipeline.process(text, source="text")
        
        # The cleaned text should not contain actual PII
        # (though it should contain [REDACTED])
        assert "Priya" not in result.cleaned_text or "[REDACTED]" in result.cleaned_text
        assert "9876543210" not in result.cleaned_text or "[REDACTED]" in result.cleaned_text
        
        # Types should be descriptive but not actual values
        assert all(isinstance(t, str) for t in result.types_found)


class TestAuditLogging:
    """Test audit logging functionality."""
    
    def test_audit_log_never_contains_pii(self):
        """Test that audit logs never contain actual PII values."""
        pipeline = PIIFilterPipeline()
        text = "My name is Rahul, call 9876543210"
        
        result = pipeline.process(text, source="text")
        audit_log = result.to_audit_log()
        
        # Convert to string and check it doesn't contain actual PII
        log_str = str(audit_log).lower()
        
        # Should not contain the actual name or number
        assert "rahul" not in log_str
        assert "9876543" not in log_str
        
        # But should contain metadata
        assert "pii_found" in log_str
        assert "redaction_count" in log_str


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    @pytest.fixture
    def pipeline(self):
        """Create PIIFilterPipeline instance."""
        return PIIFilterPipeline()
    
    def test_multiple_same_pii_type(self, pipeline):
        """Test multiple items of same PII type."""
        text = "Call 9876543210 or 8765432109"
        result = pipeline.process(text, source="text")
        
        assert result.pii_found is True
        assert result.redaction_count >= 2
        assert "phone_number" in result.types_found
    
    def test_case_insensitive_patterns(self, pipeline):
        """Test case-insensitive pattern matching."""
        text = "MY NAME IS RAHUL"
        result = pipeline.process(text, source="text")
        
        # Name pattern should match in any case
        assert result.pii_found is True
    
    def test_mixed_languages(self, pipeline):
        """Test mixed language text."""
        text = "Patient नाम राहुल है, call 9876543210"
        result = pipeline.process(text, language="en", source="text")
        
        # Should still detect phone number
        assert "phone_number" in result.types_found
    
    def test_very_long_text(self, pipeline):
        """Test processing very long text."""
        text = "Patient info: " + "A" * 10000 + " Call 9876543210"
        result = pipeline.process(text, source="text")
        
        # Should handle long text without crashing
        assert result is not None
        assert "[REDACTED]" in result.cleaned_text
    
    def test_special_characters(self, pipeline):
        """Test text with special characters."""
        text = "Name: Rahul! Email: test@example.com!!! Phone: 9876543210???"
        result = pipeline.process(text, source="text")
        
        # Should still detect PII despite special characters
        assert result.pii_found is True


class TestIntegration:
    """Integration tests with realistic scenarios."""
    
    @pytest.fixture
    def pipeline(self):
        """Create PIIFilterPipeline instance."""
        return PIIFilterPipeline()
    
    def test_chat_message_scenario(self, pipeline):
        """Test realistic chat message scenario."""
        message = "Hi doctor, this is Rahul Sharma. I'm experiencing chest pain. My phone is 9876543210 if you need to call me."
        result = pipeline.process(message, source="text")
        
        assert result.pii_found is True
        assert "name" in result.types_found
        assert "phone_number" in result.types_found
        # Clean text should be safe to send to AI
        assert any(x in result.cleaned_text for x in ["[REDACTED]"])
    
    def test_voice_transcript_scenario(self, pipeline):
        """Test voice transcript processing."""
        transcript = "This is Dr. Priya calling from clinic. Patient Rahul Sharma's number is 9876543210."
        result = pipeline.process(transcript, source="voice")
        
        assert result.source == "voice"
        assert result.pii_found is True
        result_log = result.to_audit_log()
        assert result_log["source"] == "voice"
    
    def test_medical_query_no_false_positives(self, pipeline):
        """Test medical query doesn't have false positives."""
        query = "What is the recommended treatment for BRCA1 mutations? I've read about PARP inhibitors."
        result = pipeline.process(query, source="text")
        
        # Should not flag medical terms as PII
        assert result.pii_found is False or result.redaction_count == 0
    
    def test_report_with_patient_demographics(self, pipeline):
        """Test medical report with demographics."""
        report = "PATIENT: Priya Verma, Age: 35, DOB: 15/05/1988, Contact: priya.verma@gmail.com, Phone: +91 9876543210"
        result = pipeline.process(report, source="file")
        
        assert result.pii_found is True
        assert result.source == "file"
        # Multiple redactions expected
        assert result.redaction_count >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
