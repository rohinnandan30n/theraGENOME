#!/usr/bin/env python3
"""
ClinVar Sync Script

Downloads latest ClinVar XML dump, parses variants, and syncs to PostgreSQL database.
Run periodically (e.g., weekly) to keep ClinVar data current.

Usage:
    python scripts/sync_clinvar.py [--output-path PATH] [--batch-size SIZE]
"""

import argparse
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.external_apis.clinvar import ClinVarDownloader
from src.db.variant_repository import ClinVarRepository
from src.config import CLINVAR_DOWNLOAD_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sync_clinvar(output_path: str = None, batch_size: int = 1000, keep_files: bool = False):
    """
    Sync ClinVar data to database.
    
    Args:
        output_path: Directory for downloaded files
        batch_size: Number of records per batch
        keep_files: Whether to keep downloaded files after processing
    """
    
    if output_path is None:
        output_path = CLINVAR_DOWNLOAD_PATH
    
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    try:
        # Step 1: Download ClinVar dump
        logger.info("=" * 60)
        logger.info("STEP 1: Downloading ClinVar XML dump")
        logger.info("=" * 60)
        
        gzip_path = os.path.join(output_path, 'clinvar_dump.xml.gz')
        ClinVarDownloader.download_clinvar_dump(gzip_path)
        
        # Step 2: Decompress
        logger.info("=" * 60)
        logger.info("STEP 2: Decompressing ClinVar dump")
        logger.info("=" * 60)
        
        xml_path = ClinVarDownloader.decompress_gzip(gzip_path)
        
        # Step 3: Parse and sync
        logger.info("=" * 60)
        logger.info("STEP 3: Parsing and syncing variants to database")
        logger.info("=" * 60)
        
        total_synced = 0
        total_failed = 0
        start_time = datetime.now()
        
        for batch in ClinVarDownloader.parse_clinvar_xml(xml_path, batch_size=batch_size):
            try:
                synced = ClinVarRepository.batch_upsert_clinvar_variants(batch)
                total_synced += synced
                
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = total_synced / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {total_synced} synced | Rate: {rate:.1f} variants/sec")
            
            except Exception as e:
                logger.error(f"Batch sync failed: {str(e)}")
                total_failed += len(batch)
        
        # Step 4: Cleanup
        logger.info("=" * 60)
        logger.info("STEP 4: Cleanup")
        logger.info("=" * 60)
        
        if not keep_files:
            try:
                os.remove(gzip_path)
                logger.info(f"Removed {gzip_path}")
            except Exception as e:
                logger.warning(f"Failed to remove {gzip_path}: {str(e)}")
            
            try:
                os.remove(xml_path)
                logger.info(f"Removed {xml_path}")
            except Exception as e:
                logger.warning(f"Failed to remove {xml_path}: {str(e)}")
        else:
            logger.info(f"Keeping downloaded files:")
            logger.info(f"  - {gzip_path}")
            logger.info(f"  - {xml_path}")
        
        # Final summary
        logger.info("=" * 60)
        logger.info("SYNC COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total synced: {total_synced}")
        logger.info(f"Total failed: {total_failed}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Total time: {elapsed:.1f} seconds")
        logger.info(f"Average rate: {total_synced / elapsed:.1f} variants/sec" if elapsed > 0 else "N/A")
        
        return total_synced, total_failed
    
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}", exc_info=True)
        return 0, -1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync ClinVar data to PostgreSQL database"
    )
    parser.add_argument(
        "--output-path",
        default=CLINVAR_DOWNLOAD_PATH,
        help="Output directory for downloaded files"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for database operations"
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep downloaded files after processing"
    )
    
    args = parser.parse_args()
    
    sync_clinvar(
        output_path=args.output_path,
        batch_size=args.batch_size,
        keep_files=args.keep_files
    )
