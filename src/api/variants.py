from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from datetime import datetime

from src.api.schemas import VariantRecord, VariantResponse, EnrichedVariantResponse
from src.db.variant_repository import (
    ClinVarRepository, GnomADRepository, EnrichedVariantRepository
)
from src.external_apis.gnomad import GnomADAPI
from src.cache.redis_cache import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/variants", tags=["variants"])


@router.get("/{rsid}", response_model=EnrichedVariantResponse)
async def get_variant_enriched(
    rsid: str,
    include_gnomad: bool = Query(True, description="Include gnomAD frequency data"),
    use_cache: bool = Query(True, description="Use cached data if available")
) -> EnrichedVariantResponse:
    """
    Get enriched variant data combining ClinVar and gnomAD information.
    
    - Looks up variant in ClinVar database
    - Enriches with gnomAD allele frequencies
    - Caches result in Redis with 24-hour TTL
    - Returns combined clinical and population data
    """
    
    try:
        # Check cache first
        cache_key = f"variant:{rsid}"
        if use_cache:
            cache = get_cache()
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Returning cached data for variant {rsid}")
                return EnrichedVariantResponse(**cached_data)
        
        # Try to find enriched variant in database first
        enriched = EnrichedVariantRepository.get_enriched_variant(rsid)
        
        if enriched:
            logger.info(f"Found enriched variant {rsid} in database")
            
            response_data = {
                'variant_id': rsid,
                'clinvar_data': enriched.get('clinvar_data'),
                'gnomad_data': enriched.get('gnomad_data'),
                'hgvs_mapping': enriched.get('hgvs_mapping'),
                'clinical_significance': enriched.get('clinvar_data', {}).get('clinical_significance'),
                'review_status': enriched.get('clinvar_data', {}).get('review_status'),
                'allele_frequency': enriched.get('gnomad_data', {}).get('genome_af'),
                'enriched_metadata': enriched.get('enriched_metadata')
            }
            
            response = EnrichedVariantResponse(**response_data)
            
            # Cache the result
            if use_cache:
                try:
                    cache = get_cache()
                    cache.set(cache_key, response_data)
                except Exception as e:
                    logger.warning(f"Failed to cache variant {rsid}: {str(e)}")
            
            return response
        
        # Try to fetch from ClinVar
        clinvar_data = ClinVarRepository.get_clinvar_by_variation_id(rsid)
        
        if not clinvar_data:
            raise HTTPException(
                status_code=404,
                detail=f"Variant {rsid} not found in ClinVar database"
            )
        
        # Prepare ClinVar data
        clinvar_dict = {
            'variation_id': clinvar_data.get('variation_id'),
            'rcv_id': clinvar_data.get('rcv_id'),
            'gene_symbol': clinvar_data.get('gene_symbol'),
            'hgvs_expression': clinvar_data.get('hgvs_expression'),
            'clinical_significance': clinvar_data.get('clinical_significance'),
            'review_status': clinvar_data.get('review_status'),
            'variant_type': clinvar_data.get('variant_type')
        }
        
        # Fetch gnomAD data if requested
        gnomad_dict = {}
        if include_gnomad and clinvar_data.get('ref_allele') and clinvar_data.get('alt_allele'):
            try:
                # Build gnomAD variant ID
                chrom = clinvar_dict.get('hgvs_expression', '').split(':')[0] if clinvar_dict.get('hgvs_expression') else None
                
                if chrom is None and clinvar_data.get('ref_allele'):
                    # Try alternative approach using stored ClinVar data
                    logger.debug(f"Could not extract chrom from HGVS for {rsid}")
                
                # Query gnomAD (this would need chromosome and position info)
                # For now, get from database if available
                gnomad_record = GnomADRepository.get_gnomad_by_variant_id(rsid)
                
                if gnomad_record:
                    gnomad_dict = {
                        'variant_id': gnomad_record.get('variant_id'),
                        'chrom': gnomad_record.get('chrom'),
                        'pos': gnomad_record.get('pos'),
                        'ref': gnomad_record.get('ref'),
                        'alt': gnomad_record.get('alt'),
                        'exome_af': gnomad_record.get('exome_af'),
                        'genome_af': gnomad_record.get('genome_af'),
                        'exome_ac': gnomad_record.get('exome_ac'),
                        'exome_an': gnomad_record.get('exome_an'),
                        'genome_ac': gnomad_record.get('genome_ac'),
                        'genome_an': gnomad_record.get('genome_an')
                    }
            except Exception as e:
                logger.warning(f"Failed to retrieve gnomAD data for {rsid}: {str(e)}")
        
        # Create response
        response_data = {
            'variant_id': rsid,
            'clinvar_data': clinvar_dict,
            'gnomad_data': gnomad_dict,
            'hgvs_mapping': clinvar_data.get('hgvs_expression'),
            'clinical_significance': clinvar_dict.get('clinical_significance'),
            'review_status': clinvar_dict.get('review_status'),
            'allele_frequency': gnomad_dict.get('genome_af') if gnomad_dict else None,
            'enriched_metadata': {
                'last_updated': datetime.utcnow().isoformat(),
                'data_sources': ['ClinVar', 'gnomAD'] if gnomad_dict else ['ClinVar']
            }
        }
        
        response = EnrichedVariantResponse(**response_data)
        
        # Store enriched variant in database
        try:
            EnrichedVariantRepository.create_enriched_variant(
                rsid,
                clinvar_dict,
                gnomad_dict,
                clinvar_dict.get('hgvs_expression'),
                response_data.get('enriched_metadata')
            )
        except Exception as e:
            logger.warning(f"Failed to store enriched variant {rsid}: {str(e)}")
        
        # Cache the result
        if use_cache:
            try:
                cache = get_cache()
                cache.set(cache_key, response_data)
            except Exception as e:
                logger.warning(f"Failed to cache variant {rsid}: {str(e)}")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving variant {rsid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/frequency/{chrom}/{pos}/{ref}/{alt}", response_model=dict)
async def get_allele_frequency(
    chrom: str,
    pos: int,
    ref: str,
    alt: str,
    use_cache: bool = Query(True)
) -> dict:
    """
    Get allele frequency for specific variant coordinates.
    Queries gnomAD if not in local cache.
    """
    try:
        # Build variant ID
        variant_id = GnomADAPI.parse_variant_id(chrom, pos, ref, alt)
        
        # Check cache
        cache_key = f"frequency:{variant_id}"
        if use_cache:
            try:
                cache = get_cache()
                cached = cache.get(cache_key)
                if cached:
                    return cached
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {str(e)}")
        
        # Check database
        gnomad_record = GnomADRepository.get_gnomad_by_coordinates(chrom, pos, ref, alt)
        
        if gnomad_record:
            result = {
                'variant_id': variant_id,
                'chrom': chrom,
                'pos': pos,
                'ref': ref,
                'alt': alt,
                'exome_af': gnomad_record.get('exome_af'),
                'genome_af': gnomad_record.get('genome_af'),
                'exome_ac': gnomad_record.get('exome_ac'),
                'exome_an': gnomad_record.get('exome_an'),
                'genome_ac': gnomad_record.get('genome_ac'),
                'genome_an': gnomad_record.get('genome_an')
            }
            
            # Cache it
            if use_cache:
                try:
                    cache = get_cache()
                    cache.set(cache_key, result)
                except Exception as e:
                    logger.warning(f"Cache set failed: {str(e)}")
            
            return result
        
        # Query gnomAD live
        logger.info(f"Querying gnomAD for {variant_id}")
        gnomad_data = GnomADAPI.query_variant_frequency(variant_id)
        
        if not gnomad_data:
            raise HTTPException(
                status_code=404,
                detail=f"Variant {variant_id} not found in gnomAD"
            )
        
        # Store in database
        try:
            GnomADRepository.upsert_gnomad_frequency(gnomad_data)
        except Exception as e:
            logger.warning(f"Failed to store gnomAD data: {str(e)}")
        
        # Cache result
        if use_cache:
            try:
                cache = get_cache()
                cache.set(cache_key, gnomad_data)
            except Exception as e:
                logger.warning(f"Failed to cache frequency data: {str(e)}")
        
        return gnomad_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving allele frequency: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
