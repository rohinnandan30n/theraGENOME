"""
Test suite for FileValidator.
Tests validation methods with valid and malicious inputs.
"""

import pytest
from shared.utils.file_validator import FileValidator, FileValidationError


class TestFileValidation:
    """Test FileValidator security checks."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return FileValidator()
    
    # ============ Extension Validation Tests ============
    
    def test_validate_extension_valid_single(self, validator):
        """Test validation accepts valid single extensions."""
        assert validator.validate_extension("test.vcf", [".vcf"]) is True
    
    def test_validate_extension_valid_multiple(self, validator):
        """Test validation accepts valid extensions from list."""
        assert validator.validate_extension(
            "test.vcf.gz",
            [".vcf", ".vcf.gz", ".txt"]
        ) is True
    
    def test_validate_extension_case_insensitive(self, validator):
        """Test extension validation is case-insensitive."""
        assert validator.validate_extension("test.VCF", [".vcf"]) is True
        assert validator.validate_extension("TEST.vcf", [".vcf"]) is True
    
    def test_validate_extension_no_extension(self, validator):
        """Test validation rejects files without extension."""
        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_extension("testfile", [".vcf"])
        assert "extension" in str(exc_info.value).lower()
    
    def test_validate_extension_wrong_type(self, validator):
        """Test validation rejects wrong file types."""
        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_extension("test.exe", [".vcf", ".txt"])
        assert "not allowed" in str(exc_info.value).lower()
    
    def test_validate_extension_empty_filename(self, validator):
        """Test validation rejects empty filename."""
        with pytest.raises(FileValidationError):
            validator.validate_extension("", [".vcf"])
    
    # ============ File Size Validation Tests ============
    
    def test_validate_size_within_limit(self, validator):
        """Test validation accepts files within size limit."""
        small_file = b"x" * (5 * 1024 * 1024)  # 5 MB
        assert validator.validate_size(small_file, max_mb=50) is True
    
    def test_validate_size_exact_limit(self, validator):
        """Test validation accepts file at exact size limit."""
        exact_file = b"x" * (50 * 1024 * 1024)  # 50 MB
        assert validator.validate_size(exact_file, max_mb=50) is True
    
    def test_validate_size_exceeds_limit(self, validator):
        """Test validation rejects oversized files."""
        large_file = b"x" * (51 * 1024 * 1024)  # 51 MB
        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_size(large_file, max_mb=50)
        assert "exceeds" in str(exc_info.value).lower()
        assert "50" in str(exc_info.value)
    
    def test_validate_size_empty_file(self, validator):
        """Test validation accepts empty file (no size check failure)."""
        empty_file = b""
        assert validator.validate_size(empty_file, max_mb=50) is True
    
    # ============ Magic Bytes Validation Tests ============
    
    def test_validate_magic_bytes_vcf_valid(self, validator):
        """Test VCF magic bytes validation with valid file."""
        vcf_header = b"##fileformat=VCFv4.2\n#CHROM\tPOS\tID\n"
        assert validator.validate_magic_bytes(vcf_header, "VCF") is True
    
    def test_validate_magic_bytes_vcf_invalid(self, validator):
        """Test VCF magic bytes validation rejects invalid file."""
        not_vcf = b"this is not a vcf file\n"
        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_magic_bytes(not_vcf, "VCF")
        assert "valid vcf" in str(exc_info.value).lower()
    
    def test_validate_magic_bytes_fastq_valid(self, validator):
        """Test FASTQ magic bytes validation with valid file."""
        fastq_header = b"@read1\nACGT\n+\nIIII\n"
        assert validator.validate_magic_bytes(fastq_header, "FASTQ") is True
    
    def test_validate_magic_bytes_fastq_invalid(self, validator):
        """Test FASTQ magic bytes validation rejects invalid file."""
        not_fastq = b">not a fastq file\n"
        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_magic_bytes(not_fastq, "FASTQ")
        assert "valid fastq" in str(exc_info.value).lower()
    
    def test_validate_magic_bytes_csv_valid(self, validator):
        """Test CSV magic bytes validation with valid file."""
        csv_data = b"name,age,disease\nAlice,30,cancer\nBob,25,diabetes\n"
        assert validator.validate_magic_bytes(csv_data, "CSV") is True
    
    def test_validate_magic_bytes_xml_valid_declaration(self, validator):
        """Test XML magic bytes validation with XML declaration."""
        xml_data = b"<?xml version='1.0'?>\n<root><item>test</item></root>"
        assert validator.validate_magic_bytes(xml_data, "XML") is True
    
    def test_validate_magic_bytes_xml_valid_root(self, validator):
        """Test XML magic bytes validation with just root element."""
        xml_data = b"<root><item>test</item></root>"
        assert validator.validate_magic_bytes(xml_data, "XML") is True
    
    def test_validate_magic_bytes_xml_invalid(self, validator):
        """Test XML magic bytes validation rejects invalid file."""
        not_xml = b"just some plain text content\n"
        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_magic_bytes(not_xml, "XML")
        assert "valid xml" in str(exc_info.value).lower()
    
    def test_validate_magic_bytes_txt_valid(self, validator):
        """Test TXT magic bytes validation with valid file."""
        txt_data = b"This is plain text content.\nWith multiple lines.\n"
        assert validator.validate_magic_bytes(txt_data, "TXT") is True
    
    def test_validate_magic_bytes_empty(self, validator):
        """Test magic bytes validation rejects empty file."""
        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_magic_bytes(b"", "VCF")
        assert "empty" in str(exc_info.value).lower()
    
    def test_validate_magic_bytes_audio_skip(self, validator):
        """Test audio file types skip magic byte validation."""
        dummy_audio = b"dummy audio content"
        # Should not raise for audio types
        assert validator.validate_magic_bytes(dummy_audio, "WAV") is True
        assert validator.validate_magic_bytes(dummy_audio, "MP3") is True
        assert validator.validate_magic_bytes(dummy_audio, "OGG") is True
    
    # ============ Filename Sanitization Tests ============
    
    def test_sanitize_filename_normal(self, validator):
        """Test sanitization preserves normal filenames."""
        assert validator.sanitize_filename("patient_data.vcf") == "patient_data.vcf"
        assert validator.sanitize_filename("test-file_123.txt") == "test-file_123.txt"
    
    def test_sanitize_filename_path_traversal_unix(self, validator):
        """Test sanitization removes Unix path traversal."""
        assert validator.sanitize_filename("../../etc/passwd") == "etcpasswd"
        assert "../../../secret.txt" not in validator.sanitize_filename("../../../secret.txt")
    
    def test_sanitize_filename_path_traversal_windows(self, validator):
        """Test sanitization removes Windows path traversal."""
        assert validator.sanitize_filename("..\\..\\windows\\system32\\config") == "windowssystem32config"
    
    def test_sanitize_filename_special_chars(self, validator):
        """Test sanitization removes special characters."""
        safe = validator.sanitize_filename("test<script>.vcf")
        assert "<" not in safe
        assert ">" not in safe
        assert "script" in safe
    
    def test_sanitize_filename_spaces(self, validator):
        """Test sanitization removes spaces."""
        safe = validator.sanitize_filename("my test file.txt")
        assert " " not in safe
        assert "mytestfile.txt" == safe or "my-test-file.txt" == safe or "mytestfile.txt" == safe
    
    def test_sanitize_filename_leading_dots(self, validator):
        """Test sanitization removes leading dots."""
        assert validator.sanitize_filename(".hidden.vcf") == "hidden.vcf"
    
    def test_sanitize_filename_truncation(self, validator):
        """Test sanitization truncates long filenames."""
        long_name = "a" * 500 + ".txt"
        safe = validator.sanitize_filename(long_name)
        assert len(safe) <= 255
    
    def test_sanitize_filename_empty(self, validator):
        """Test sanitization handles empty filename."""
        safe = validator.sanitize_filename("")
        assert safe == "file"
    
    # ============ Malicious Content Scanning Tests ============
    
    def test_scan_null_bytes(self, validator):
        """Test scanning detects null byte injection."""
        content = b"normal content" + b"\x00" + b"hidden payload"
        with pytest.raises(FileValidationError) as exc_info:
            validator.scan_for_malicious_content(content)
        assert "null" in str(exc_info.value).lower()
    
    def test_scan_script_tag(self, validator):
        """Test scanning detects embedded script tags."""
        malicious = b"normal data\n<script>alert('xss')</script>\n"
        with pytest.raises(FileValidationError) as exc_info:
            validator.scan_for_malicious_content(malicious)
        assert "malicious" in str(exc_info.value).lower()
    
    def test_scan_php_tag(self, validator):
        """Test scanning detects PHP tags."""
        malicious = b"data, data\n<?php system('rm -rf /'); ?>\n"
        with pytest.raises(FileValidationError) as exc_info:
            validator.scan_for_malicious_content(malicious)
        assert "malicious" in str(exc_info.value).lower()
    
    def test_scan_eval_function(self, validator):
        """Test scanning detects eval() calls."""
        malicious = b"import sys\neval(user_input)\n"
        with pytest.raises(FileValidationError) as exc_info:
            validator.scan_for_malicious_content(malicious)
        assert "malicious" in str(exc_info.value).lower()
    
    def test_scan_exec_function(self, validator):
        """Test scanning detects exec() calls."""
        malicious = b"exec(dangerous_code)"
        with pytest.raises(FileValidationError) as exc_info:
            validator.scan_for_malicious_content(malicious)
        assert "malicious" in str(exc_info.value).lower()
    
    def test_scan_subprocess_module(self, validator):
        """Test scanning detects subprocess module usage."""
        malicious = b"import subprocess\nsubprocess.run(...)"
        with pytest.raises(FileValidationError) as exc_info:
            validator.scan_for_malicious_content(malicious)
        assert "malicious" in str(exc_info.value).lower()
    
    def test_scan_long_line_buffer_overflow(self, validator):
        """Test scanning detects excessively long lines."""
        # Create content with a line over 10000 characters
        long_line = b"A" * 15000
        with pytest.raises(FileValidationError) as exc_info:
            validator.scan_for_malicious_content(long_line)
        assert "long" in str(exc_info.value).lower()
    
    def test_scan_clean_content(self, validator):
        """Test scanning accepts clean content."""
        clean_vcf = b"##fileformat=VCFv4.2\n#CHROM\tPOS\tID\nREF\nALT\n"
        assert validator.scan_for_malicious_content(clean_vcf) is True
    
    def test_scan_case_insensitive(self, validator):
        """Test scanning is case-insensitive for malicious patterns."""
        malicious = b"EVAL(code)"
        with pytest.raises(FileValidationError):
            validator.scan_for_malicious_content(malicious)
    
    # ============ Integration Tests ============
    
    def test_complete_vcf_validation_flow(self, validator):
        """Test complete validation flow for VCF file."""
        filename = "patient_variants.vcf"
        content = b"##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\n"
        
        # All checks should pass
        assert validator.validate_extension(filename, [".vcf", ".vcf.gz"]) is True
        assert validator.validate_size(content, max_mb=50) is True
        assert validator.validate_magic_bytes(content, "VCF") is True
        safe_name = validator.sanitize_filename(filename)
        assert safe_name == "patient_variants.vcf"
        assert validator.scan_for_malicious_content(content) is True
    
    def test_malicious_vcf_file_injection(self, validator):
        """Test detection of malicious content in VCF filename."""
        malicious_name = "../../etc/passwd.vcf"
        safe_name = validator.sanitize_filename(malicious_name)
        assert ".." not in safe_name
        assert "/" not in safe_name
    
    def test_disguised_executable_as_txt(self, validator):
        """Test detection of executable code disguised as text."""
        disguised = b"genome_data.txt content\n<?php system('whoami'); ?>\n"
        with pytest.raises(FileValidationError):
            validator.scan_for_malicious_content(disguised)
    
    def test_fastq_with_php_injection(self, validator):
        """Test FASTQ file with PHP injection attempt."""
        content = b"@sequence\nACGT<?php echo 'hacked' ?>\n+\nIIII\n"
        # Should fail magic bytes check or malicious content check
        try:
            validator.validate_magic_bytes(content, "FASTQ")
            # If it passes magic bytes, it should fail malicious content scan
            validator.scan_for_malicious_content(content)
            assert False, "Should have detected PHP injection"
        except FileValidationError:
            pass  # Expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
