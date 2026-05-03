import uuid
from typing import List, Dict, Any, Optional
from src.db.connection import db
import logging
import json

logger = logging.getLogger(__name__)


class ClinVarRepository:
    """Data access for ClinVar variants"""
    
    @staticmethod
    def upsert_clinvar_variant(variant_data: Dict[str, Any]) -> bool:
        """Insert or update ClinVar variant record"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO clinvar_variants 
                    (variation_id, rcv_id, gene_symbol, hgvs_expression, 
                     variant_type, ref_allele, alt_allele, clinical_significance, 
                     review_status, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (variation_id) DO UPDATE SET
                        gene_symbol = EXCLUDED.gene_symbol,
                        hgvs_expression = EXCLUDED.hgvs_expression,
                        clinical_significance = EXCLUDED.clinical_significance,
                        review_status = EXCLUDED.review_status,
                        last_updated = EXCLUDED.last_updated,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        variant_data.get('variation_id'),
                        variant_data.get('rcv_id'),
                        variant_data.get('gene_symbol'),
                        variant_data.get('hgvs_expression'),
                        variant_data.get('variant_type'),
                        variant_data.get('ref_allele'),
                        variant_data.get('alt_allele'),
                        variant_data.get('clinical_significance'),
                        variant_data.get('review_status'),
                        variant_data.get('last_updated')
                    )
                )
            return True
        except Exception as e:
            logger.error(f"Error upserting ClinVar variant: {str(e)}")
            return False

    @staticmethod
    def batch_upsert_clinvar_variants(variants: List[Dict[str, Any]]) -> int:
        """Batch insert/update ClinVar variants"""
        inserted = 0
        
        for variant in variants:
            try:
                if ClinVarRepository.upsert_clinvar_variant(variant):
                    inserted += 1
            except Exception as e:
                logger.warning(f"Error upserting variant {variant.get('variation_id')}: {str(e)}")
                continue
        
        logger.info(f"Batch upserted {inserted}/{len(variants)} ClinVar variants")
        return inserted

    @staticmethod
    def get_clinvar_by_variation_id(variation_id: str) -> Optional[Dict[str, Any]]:
        """Get ClinVar variant by variation ID"""
        with db.get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM clinvar_variants WHERE variation_id = %s",
                (variation_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def get_clinvar_by_hgvs(hgvs_expression: str) -> Optional[Dict[str, Any]]:
        """Get ClinVar variant by HGVS expression"""
        with db.get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM clinvar_variants WHERE hgvs_expression = %s",
                (hgvs_expression,)
            )
            return cursor.fetchone()

    @staticmethod
    def get_clinvar_by_gene(gene_symbol: str) -> List[Dict[str, Any]]:
        """Get all ClinVar variants for a gene"""
        with db.get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM clinvar_variants WHERE gene_symbol = %s",
                (gene_symbol,)
            )
            return cursor.fetchall()


class GnomADRepository:
    """Data access for gnomAD frequency data"""
    
    @staticmethod
    def upsert_gnomad_frequency(gnomad_data: Dict[str, Any], clinvar_variation_id: Optional[str] = None) -> bool:
        """Insert or update gnomAD frequency data"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO gnomad_frequencies
                    (variant_id, clinvar_variation_id, chrom, pos, ref, alt, 
                     exome_ac, exome_an, exome_af, genome_ac, genome_an, genome_af, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (variant_id) DO UPDATE SET
                        exome_ac = EXCLUDED.exome_ac,
                        exome_an = EXCLUDED.exome_an,
                        exome_af = EXCLUDED.exome_af,
                        genome_ac = EXCLUDED.genome_ac,
                        genome_an = EXCLUDED.genome_an,
                        genome_af = EXCLUDED.genome_af,
                        last_updated = CURRENT_TIMESTAMP
                    """,
                    (
                        gnomad_data.get('variant_id'),
                        clinvar_variation_id,
                        gnomad_data.get('chrom'),
                        gnomad_data.get('pos'),
                        gnomad_data.get('ref'),
                        gnomad_data.get('alt'),
                        gnomad_data.get('exome_ac'),
                        gnomad_data.get('exome_an'),
                        gnomad_data.get('exome_af'),
                        gnomad_data.get('genome_ac'),
                        gnomad_data.get('genome_an'),
                        gnomad_data.get('genome_af')
                    )
                )
            return True
        except Exception as e:
            logger.error(f"Error upserting gnomAD data: {str(e)}")
            return False

    @staticmethod
    def get_gnomad_by_variant_id(variant_id: str) -> Optional[Dict[str, Any]]:
        """Get gnomAD frequency data by variant ID"""
        with db.get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM gnomad_frequencies WHERE variant_id = %s",
                (variant_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def get_gnomad_by_coordinates(chrom: str, pos: int, ref: str, alt: str) -> Optional[Dict[str, Any]]:
        """Get gnomAD data by genomic coordinates"""
        with db.get_cursor(commit=False) as cursor:
            cursor.execute(
                """SELECT * FROM gnomad_frequencies 
                   WHERE chrom = %s AND pos = %s AND ref = %s AND alt = %s""",
                (chrom, pos, ref, alt)
            )
            return cursor.fetchone()


class EnrichedVariantRepository:
    """Data access for enriched variant data"""
    
    @staticmethod
    def create_enriched_variant(variant_id: str, clinvar_data: Dict, gnomad_data: Dict, 
                                hgvs_mapping: Optional[str] = None, metadata: Optional[Dict] = None) -> bool:
        """Create an enriched variant record"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO enriched_variants
                    (variant_id, clinvar_data, gnomad_data, hgvs_mapping, enriched_metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (variant_id) DO UPDATE SET
                        clinvar_data = EXCLUDED.clinvar_data,
                        gnomad_data = EXCLUDED.gnomad_data,
                        hgvs_mapping = EXCLUDED.hgvs_mapping,
                        enriched_metadata = EXCLUDED.enriched_metadata,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        variant_id,
                        json.dumps(clinvar_data),
                        json.dumps(gnomad_data),
                        hgvs_mapping,
                        json.dumps(metadata) if metadata else None
                    )
                )
            return True
        except Exception as e:
            logger.error(f"Error creating enriched variant: {str(e)}")
            return False

    @staticmethod
    def get_enriched_variant(variant_id: str) -> Optional[Dict[str, Any]]:
        """Get enriched variant data"""
        with db.get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM enriched_variants WHERE variant_id = %s",
                (variant_id,)
            )
            result = cursor.fetchone()
            
            if result:
                # Parse JSON fields
                result['clinvar_data'] = json.loads(result.get('clinvar_data', '{}'))
                result['gnomad_data'] = json.loads(result.get('gnomad_data', '{}'))
                result['enriched_metadata'] = json.loads(result.get('enriched_metadata', '{}'))
            
            return result
