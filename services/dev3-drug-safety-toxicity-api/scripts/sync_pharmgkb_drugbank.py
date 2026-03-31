#!/usr/bin/env python3
"""
ETL script to sync drug data and PGx recommendations from PharmGKB and DrugBank.
Run periodically (e.g., weekly) to keep the database up to date.

Usage: python scripts/sync_pharmgkb_drugbank.py
"""
import asyncio
import logging
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.connection import AsyncSessionLocal, get_db_session
from src.db.drug_safety_repository import DrugRepository, PGxRepository
from src.schemas.drug_schema import Drug, PGxRecommendation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PHARMGKB_BASE = "https://api.pharmgkb.org/v1"


async def sync_drugs_from_pharmgkb():
    """Fetch and sync drugs from PharmGKB."""
    logger.info("Starting PharmGKB drug sync...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Fetch chemicals from PharmGKB (this is a simplified example)
            resp = await client.get(
                f"{PHARMGKB_BASE}/chemical",
                params={"view": "base", "limit": 100},
            )
            resp.raise_for_status()
            chemicals = resp.json().get("data", [])

            async with AsyncSessionLocal() as session:
                drug_repo = DrugRepository(session)

                for chem in chemicals:
                    try:
                        existing = await drug_repo.get_by_name(chem.get("name"))
                        if not existing:
                            await drug_repo.create({
                                "name": chem.get("name"),
                                "description": chem.get("description"),
                                "category": "chemical",
                            })
                            logger.info(f"✅ Added drug: {chem.get('name')}")
                    except Exception as e:
                        logger.warning(f"Error syncing drug {chem.get('name')}: {e}")

            logger.info(f"✅ Synced {len(chemicals)} drugs from PharmGKB")

        except httpx.RequestError as e:
            logger.error(f"PharmGKB request error: {e}")
        except Exception as e:
            logger.error(f"Error syncing drugs: {e}")


async def sync_pgx_recommendations():
    """Fetch and sync PGx recommendations from PharmGKB."""
    logger.info("Starting PGx recommendation sync...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Fetch clinical annotations from PharmGKB
            resp = await client.get(
                f"{PHARMGKB_BASE}/clinicalAnnotation",
                params={"view": "full", "limit": 100},
            )
            resp.raise_for_status()
            annotations = resp.json().get("data", [])

            async with AsyncSessionLocal() as session:
                drug_repo = DrugRepository(session)
                pgx_repo = PGxRepository(session)

                for annot in annotations:
                    try:
                        # Find or create drug
                        drug_name = annot.get("drug", {}).get("name")
                        gene_name = annot.get("gene", {}).get("symbol")

                        if not drug_name or not gene_name:
                            continue

                        drug = await drug_repo.get_by_name(drug_name)
                        if not drug:
                            drug = await drug_repo.create({
                                "name": drug_name,
                                "category": "drug",
                            })

                        # Check if PGx recommendation already exists
                        existing = await pgx_repo.get_by_gene_and_drug(gene_name, drug.id)
                        if not existing:
                            await pgx_repo.create({
                                "gene": gene_name,
                                "drug_id": drug.id,
                                "recommendation": annot.get("text", ""),
                                "evidence_level": annot.get("evidenceLevel"),
                                "phenotype_categories": annot.get("phenotypeCategories", []),
                                "source": "PharmGKB",
                                "pharmgkb_url": f"https://www.pharmgkb.org/clinicalAnnotation/{annot.get('id')}",
                            })
                            logger.info(f"✅ Added PGx: {gene_name} + {drug_name}")

                    except Exception as e:
                        logger.warning(f"Error syncing PGx {gene_name}: {e}")

            logger.info(f"✅ Synced {len(annotations)} PGx recommendations")

        except httpx.RequestError as e:
            logger.error(f"PharmGKB request error: {e}")
        except Exception as e:
            logger.error(f"Error syncing PGx recommendations: {e}")


async def main():
    """Main function."""
    logger.info(f"🚀 Starting ETL sync at {datetime.now().isoformat()}")

    try:
        await sync_drugs_from_pharmgkb()
        await sync_pgx_recommendations()

        logger.info(f"✅ ETL sync completed at {datetime.now().isoformat()}")

    except Exception as e:
        logger.error(f"Fatal error during ETL sync: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
