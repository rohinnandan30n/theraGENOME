import requests
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GnomADAPI:
    """Integration with gnomAD GraphQL API for allele frequency data"""
    
    GNOMAD_GRAPHQL_URL = "https://gnomad.broadinstitute.org/api"
    
    # GraphQL query template for variant lookup
    VARIANT_QUERY = """
    query VariantDetail($variantId: String!) {
        variant(variantId: $variantId) {
            variantId
            chrom
            pos
            ref
            alt
            exomeFreq: freq(dataset: gnomad_r2_1_exomes) {
                ac
                an
                af
            }
            genomeFreq: freq(dataset: gnomad_r2_1_genomes) {
                ac
                an
                af
            }
        }
    }
    """
    
    # GraphQL query for population breakdown
    POPULATION_QUERY = """
    query VariantPopulations($variantId: String!) {
        variant(variantId: $variantId) {
            variantId
            populations: freq(dataset: gnomad_r2_1_genomes) {
                popmax {
                    pop
                    ac
                    an
                    af
                }
            }
        }
    }
    """
    
    @staticmethod
    def query_variant_frequency(variant_id: str) -> Optional[Dict[str, Any]]:
        """
        Query gnomAD for variant allele frequency data.
        
        variant_id format: "1-12345-A-T" (chrom-pos-ref-alt)
        """
        logger.info(f"Querying gnomAD for variant: {variant_id}")
        
        try:
            response = requests.post(
                GnomADAPI.GNOMAD_GRAPHQL_URL,
                json={
                    'query': GnomADAPI.VARIANT_QUERY,
                    'variables': {'variantId': variant_id}
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'errors' in data:
                logger.warning(f"GraphQL errors from gnomAD: {data['errors']}")
                return None
            
            variant_data = data.get('data', {}).get('variant')
            
            if not variant_data:
                logger.warning(f"No data returned for variant {variant_id}")
                return None
            
            # Extract frequency data
            result = {
                'variant_id': variant_data.get('variantId'),
                'chrom': variant_data.get('chrom'),
                'pos': variant_data.get('pos'),
                'ref': variant_data.get('ref'),
                'alt': variant_data.get('alt'),
                'exome_ac': None,
                'exome_an': None,
                'exome_af': None,
                'genome_ac': None,
                'genome_an': None,
                'genome_af': None
            }
            
            # Extract exome frequencies
            exome_freq = variant_data.get('exomeFreq')
            if exome_freq:
                result['exome_ac'] = exome_freq.get('ac')
                result['exome_an'] = exome_freq.get('an')
                result['exome_af'] = exome_freq.get('af')
            
            # Extract genome frequencies
            genome_freq = variant_data.get('genomeFreq')
            if genome_freq:
                result['genome_ac'] = genome_freq.get('ac')
                result['genome_an'] = genome_freq.get('an')
                result['genome_af'] = genome_freq.get('af')
            
            logger.debug(f"Retrieved gnomAD data for {variant_id}")
            return result
        
        except requests.RequestException as e:
            logger.error(f"gnomAD API request failed: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse gnomAD response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error querying gnomAD: {str(e)}")
            return None

    @staticmethod
    def query_population_frequencies(variant_id: str) -> Optional[Dict[str, Any]]:
        """Query population-specific allele frequencies from gnomAD"""
        logger.info(f"Querying gnomAD populations for variant: {variant_id}")
        
        try:
            response = requests.post(
                GnomADAPI.GNOMAD_GRAPHQL_URL,
                json={
                    'query': GnomADAPI.POPULATION_QUERY,
                    'variables': {'variantId': variant_id}
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'errors' in data:
                logger.warning(f"GraphQL errors from gnomAD: {data['errors']}")
                return None
            
            return data.get('data', {}).get('variant')
        
        except Exception as e:
            logger.error(f"Failed to query gnomAD populations: {str(e)}")
            return None

    @staticmethod
    def parse_variant_id(chrom: str, pos: int, ref: str, alt: str) -> str:
        """Convert genomic coordinates to gnomAD variant ID format"""
        return f"{chrom}-{pos}-{ref}-{alt}"

    @staticmethod
    def parse_variant_coordinates(variant_id: str) -> Optional[Dict[str, Any]]:
        """Parse gnomAD variant ID to extract coordinates"""
        try:
            parts = variant_id.split('-')
            if len(parts) != 4:
                return None
            
            return {
                'chrom': parts[0],
                'pos': int(parts[1]),
                'ref': parts[2],
                'alt': parts[3]
            }
        except Exception as e:
            logger.error(f"Failed to parse variant ID {variant_id}: {str(e)}")
            return None
