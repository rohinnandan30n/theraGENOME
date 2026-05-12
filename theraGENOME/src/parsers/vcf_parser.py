from typing import List, Dict, Any, TextIO
import logging

logger = logging.getLogger(__name__)


class VCFParser:
    """Parser for VCF (Variant Call Format) files"""
    
    # Standard VCF header fields
    REQUIRED_FIELDS = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO', 'FORMAT']
    FIXED_FIELDS = ['CHROM', 'POS', 'REF', 'ALT', 'QUAL', 'INFO']
    
    def __init__(self):
        self.header_lines = []
        self.field_indices = {}
    
    def validate_vcf_file(self, file_content: str) -> bool:
        """Validate VCF file format"""
        lines = file_content.strip().split('\n')
        
        # Check for VCF magic number
        if not lines or not lines[0].startswith('##fileformat=VCFv'):
            raise ValueError("Invalid VCF file: missing or incorrect fileformat declaration")
        
        # Find header line
        header_line = None
        header_idx = 0
        for idx, line in enumerate(lines):
            if line.startswith('#CHROM'):
                header_line = line
                header_idx = idx
                break
        
        if not header_line:
            raise ValueError("Invalid VCF file: missing #CHROM header line")
        
        self.header_lines = lines[:header_idx + 1]
        return True
    
    def parse_header(self, header_line: str) -> Dict[str, int]:
        """Parse VCF header line to get field indices"""
        fields = header_line.lstrip('#').split('\t')
        
        # Validate required fields
        for required_field in self.FIXED_FIELDS:
            if required_field not in fields:
                raise ValueError(f"Missing required VCF field: {required_field}")
        
        field_indices = {field: idx for idx, field in enumerate(fields)}
        self.field_indices = field_indices
        return field_indices
    
    def parse_variant_record(self, record_line: str) -> Dict[str, Any]:
        """Parse a single variant record line"""
        fields = record_line.strip().split('\t')
        
        if len(fields) < len(self.FIXED_FIELDS):
            raise ValueError(f"Incomplete variant record: {record_line}")
        
        try:
            chrom = fields[self.field_indices['CHROM']]
            pos = int(fields[self.field_indices['POS']])
            ref = fields[self.field_indices['REF']]
            alt = fields[self.field_indices['ALT']]
            qual_str = fields[self.field_indices['QUAL']]
            qual = float(qual_str) if qual_str != '.' else None
            info = fields[self.field_indices['INFO']]
            
            return {
                'chrom': chrom,
                'pos': pos,
                'ref': ref,
                'alt': alt,
                'qual': qual,
                'info': info
            }
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing variant record: {str(e)}")
            raise ValueError(f"Failed to parse variant record: {str(e)}")
    
    def parse(self, file_content: str) -> List[Dict[str, Any]]:
        """Parse entire VCF file and return list of variant records"""
        lines = file_content.strip().split('\n')
        
        # Validate file format
        self.validate_vcf_file(file_content)
        
        # Find and parse header
        header_line = None
        data_start_idx = 0
        for idx, line in enumerate(lines):
            if line.startswith('#CHROM'):
                header_line = line
                data_start_idx = idx + 1
                break
        
        if not header_line:
            raise ValueError("No #CHROM header line found")
        
        self.parse_header(header_line)
        
        # Parse variant records
        variants = []
        for idx, line in enumerate(lines[data_start_idx:], start=data_start_idx):
            if line.startswith('#') or not line.strip():
                continue
            
            try:
                variant = self.parse_variant_record(line)
                variants.append(variant)
            except ValueError as e:
                logger.warning(f"Skipping invalid record at line {idx + 1}: {str(e)}")
                continue
        
        logger.info(f"Parsed {len(variants)} variant records from VCF file")
        return variants


def parse_vcf_file(file_content: str) -> List[Dict[str, Any]]:
    """Convenience function to parse VCF file"""
    parser = VCFParser()
    return parser.parse(file_content)
