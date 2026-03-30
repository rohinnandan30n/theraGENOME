import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import gzip
import io

logger = logging.getLogger(__name__)


class ClinVarDownloader:
    """Download and parse ClinVar XML dump"""
    
    CLINVAR_FTP_URL = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/xml/clinvar_variations.xml.gz"
    CLINVAR_RELEASE_URL = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/xml/clinvar_variations.xml.gz"
    
    @staticmethod
    def download_clinvar_dump(output_path: str = './clinvar_dump.xml.gz') -> str:
        """Download latest ClinVar XML dump"""
        logger.info(f"Downloading ClinVar dump from {ClinVarDownloader.CLINVAR_FTP_URL}")
        
        try:
            response = requests.get(
                ClinVarDownloader.CLINVAR_FTP_URL,
                stream=True,
                timeout=300
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # Log every 1MB
                                logger.info(f"Downloaded {percent:.1f}%")
            
            logger.info(f"ClinVar dump downloaded to {output_path}")
            return output_path
        
        except requests.RequestException as e:
            logger.error(f"Failed to download ClinVar dump: {str(e)}")
            raise

    @staticmethod
    def decompress_gzip(gzip_path: str) -> str:
        """Decompress gzip file"""
        xml_path = gzip_path.replace('.gz', '')
        
        logger.info(f"Decompressing {gzip_path} to {xml_path}")
        
        try:
            with gzip.open(gzip_path, 'rb') as f_in:
                with open(xml_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            logger.info(f"Decompressed to {xml_path}")
            return xml_path
        
        except Exception as e:
            logger.error(f"Failed to decompress file: {str(e)}")
            raise

    @staticmethod
    def parse_clinvar_xml(xml_path: str, batch_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Parse ClinVar XML dump and extract variant records.
        Returns list of variant dictionaries (generator for memory efficiency)
        """
        logger.info(f"Parsing ClinVar XML from {xml_path}")
        
        variants = []
        record_count = 0
        
        try:
            context = ET.iterparse(xml_path, events=('end',))
            
            for event, elem in context:
                if elem.tag == 'VariationArchive':
                    try:
                        variant = ClinVarDownloader._extract_variant_record(elem)
                        if variant:
                            variants.append(variant)
                            record_count += 1
                        
                        # Log progress and yield in batches
                        if record_count % batch_size == 0:
                            logger.info(f"Parsed {record_count} records")
                            if len(variants) >= batch_size:
                                yield variants
                                variants = []
                    
                    except Exception as e:
                        logger.warning(f"Error parsing variant record: {str(e)}")
                        continue
                    
                    finally:
                        # Clear element to save memory
                        elem.clear()
            
            # Yield remaining records
            if variants:
                yield variants
            
            logger.info(f"Completed parsing {record_count} total records")
            
        except Exception as e:
            logger.error(f"Failed to parse ClinVar XML: {str(e)}")
            raise

    @staticmethod
    def _extract_variant_record(variation_archive_elem) -> Optional[Dict[str, Any]]:
        """Extract variant data from VariationArchive XML element"""
        
        try:
            variation_id = variation_archive_elem.get('VariationID')
            variation_set = variation_archive_elem.find('VariationSet')
            
            if variation_set is None:
                return None
            
            # Extract HGVS expression
            hgvs_expression = None
            clinvar_assertion = variation_archive_elem.find('ClinVarAssertion')
            if clinvar_assertion is not None:
                hgvs_elem = clinvar_assertion.find('HGVSListSet/HGVS/NucleotideExpression')
                if hgvs_elem is not None:
                    hgvs_expression = hgvs_elem.get('sequence')
            
            # Extract gene symbol
            gene_symbol = None
            gene_elem = variation_set.find('.//Gene')
            if gene_elem is not None:
                gene_symbol = gene_elem.get('Symbol')
            
            # Extract review status and clinical significance
            review_status = None
            clinical_significance = None
            assertion = variation_archive_elem.find('.//ClassifiedRecord/ClassificationSet/Classification')
            
            if assertion is not None:
                # Review status from ReviewSet
                review_set = assertion.find('ReviewSet')
                if review_set is not None:
                    review_status = review_set.get('ReviewCount', '0')
                
                # Clinical significance
                clinical_sig_elem = assertion.find('Description')
                if clinical_sig_elem is not None:
                    clinical_significance = clinical_sig_elem.text
            
            # Extract RCV identifier
            rcv_id = variation_archive_elem.find('.//ClinVarAssertion/ClinVarSubmissionID')
            rcv_str = rcv_id.get('localKey') if rcv_id is not None else None
            
            # Extract variant type
            variant_type = variation_archive_elem.get('VariationType')
            
            # Extract allele information
            allele = variation_set.find('.//Allele')
            ref_allele = None
            alt_allele = None
            
            if allele is not None:
                sequence = allele.find('Sequence')
                if sequence is not None:
                    alt_allele = sequence.get('Seq')
                
                variant_in_source = allele.find('VariantInSingleSource')
                if variant_in_source is not None:
                    ref_allele = variant_in_source.get('RefAllele')
            
            last_updated = variation_archive_elem.get('DateLast')
            
            return {
                'variation_id': variation_id,
                'rcv_id': rcv_str,
                'gene_symbol': gene_symbol,
                'hgvs_expression': hgvs_expression,
                'variant_type': variant_type,
                'ref_allele': ref_allele,
                'alt_allele': alt_allele,
                'clinical_significance': clinical_significance,
                'review_status': review_status,
                'last_updated': datetime.fromisoformat(last_updated) if last_updated else None
            }
        
        except Exception as e:
            logger.warning(f"Failed to extract variant record: {str(e)}")
            return None
