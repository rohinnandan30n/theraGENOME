#!/usr/bin/env python3
"""
ETL script to sync adverse event data from FDA FAERS via openFDA API.
Run periodically (e.g., weekly) to update adverse event records.

Usage: python scripts/sync_faers.py
"""
import asyncio
import logging
import httpx
from datetime import datetime
from collections import Counter

from src.db.connection import AsyncSessionLocal
from src.db.drug_safety_repository import DrugRepository, AdverseEventRepository
from src.schemas.drug_schema import AdverseEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENFDA_URL = "https://api.fda.gov/drug/event.json"


async def fetch_faers_data_for_drug(drug_name: str, limit: int = 100) -> dict:
    """Fetch adverse events for a specific drug from openFDA."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                OPENFDA_URL,
                params={
                    "search": f"patient.drug.medicinalproduct:{drug_name}",
                    "limit": limit,
                },
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            logger.warning(f"FAERS request error for {drug_name}: {e}")
            return {}


async def sync_faers_for_drugs(drug_names: list = None):
    """Sync FAERS adverse events for specified drugs."""
    logger.info("Starting FAERS adverse event sync...")

    # Default drugs to sync (can be made configurable)
    if not drug_names:
        drug_names = [
            "aspirin",
            "ibuprofen",
            "metformin",
            "simvastatin",
            "warfarin",
            "clopidogrel",
            "lisinopril",
            "amoxicillin",
        ]

    async with AsyncSessionLocal() as session:
        drug_repo = DrugRepository(session)
        ae_repo = AdverseEventRepository(session)

        for drug_name in drug_names:
            try:
                logger.info(f"Fetching FAERS data for {drug_name}...")
                faers_data = await fetch_faers_data_for_drug(drug_name)

                if not faers_data.get("results"):
                    logger.info(f"No FAERS results for {drug_name}")
                    continue

                # Find or create drug record
                drug = await drug_repo.get_by_name(drug_name)
                if not drug:
                    drug = await drug_repo.create({
                        "name": drug_name,
                        "category": "drug",
                    })
                    logger.info(f"✅ Created drug record: {drug_name}")

                # Parse reactions
                results = faers_data.get("results", [])
                reaction_counter = Counter()
                outcome_counter = Counter()

                for result in results:
                    try:
                        patient = result.get("patient", {})
                        reactions = patient.get("reaction", [])
                        outcomes = patient.get("outcome", [])

                        for reaction in reactions:
                            reaction_type = reaction.get("reactionmeddrapt", "Unknown")
                            reaction_counter[reaction_type] += 1

                        for outcome in outcomes:
                            outcome_type = outcome.get("patientoutcome", "Unknown")
                            outcome_counter[outcome_type] += 1

                    except Exception as e:
                        logger.warning(f"Error parsing FAERS result: {e}")
                        continue

                # Store aggregated adverse events
                for reaction_type, count in reaction_counter.most_common(10):
                    try:
                        # Check if record already exists
                        existing_events = await ae_repo.get_by_drug_id(drug.id)
                        existing = next(
                            (e for e in existing_events if e.event_type.lower() == reaction_type.lower()),
                            None
                        )

                        if existing:
                            # Update count
                            existing.event_count = count
                            session.add(existing)
                        else:
                            # Create new
                            await ae_repo.create({
                                "drug_id": drug.id,
                                "event_type": reaction_type,
                                "event_count": count,
                                "seriousness_level": "unknown",
                                "outcomes": dict(outcome_counter),
                                "source": "FDA-FAERS",
                            })
                        logger.info(f"✅ Synced adverse event: {drug_name} - {reaction_type} ({count})")

                    except Exception as e:
                        logger.warning(f"Error storing adverse event: {e}")

                await session.commit()
                total_results = faers_data.get("meta", {}).get("results", {}).get("total", 0)
                logger.info(f"✅ Synced FAERS data for {drug_name} ({total_results} total reports)")

            except Exception as e:
                logger.error(f"Error syncing FAERS for {drug_name}: {e}")
                await session.rollback()


async def main():
    """Main function."""
    logger.info(f"🚀 Starting FAERS sync at {datetime.now().isoformat()}")

    try:
        await sync_faers_for_drugs()
        logger.info(f"✅ FAERS sync completed at {datetime.now().isoformat()}")

    except Exception as e:
        logger.error(f"Fatal error during FAERS sync: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
