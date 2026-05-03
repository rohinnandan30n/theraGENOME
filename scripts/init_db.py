#!/usr/bin/env python3
"""
Initialize database schema for variant database integration.

Creates tables for:
- ClinVar variants
- gnomAD frequencies
- Enriched variant data
"""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.db.connection import db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_variant_database():
    """Initialize variant database schema"""
    
    logger.info("Initializing variant database schema...")
    
    try:
        # Read schema file
        schema_file = os.path.join(
            os.path.dirname(__file__),
            '..',
            'src',
            'schemas',
            'variant_integration_schema.sql'
        )
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        with db.get_cursor() as cursor:
            cursor.execute(schema_sql)
        
        logger.info("Database schema initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    if init_variant_database():
        logger.info("Database initialization complete")
        sys.exit(0)
    else:
        logger.error("Database initialization failed")
        sys.exit(1)
