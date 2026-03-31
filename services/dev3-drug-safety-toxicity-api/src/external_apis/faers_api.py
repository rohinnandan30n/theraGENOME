import httpx
import logging
from src.cache.redis_cache import cache_get, cache_set, CacheKeyBuilder
from typing import Optional

logger = logging.getLogger(__name__)

OPENFDA_URL = "https://api.fda.gov/drug/event.json"


async def get_adverse_events(drug_name: str, limit: int = 10) -> dict:
    """
    Fetch adverse event reports for a drug from FDA openFDA.
    Caches results for efficiency.
    """
    cache_key = CacheKeyBuilder.faers(drug_name)

    # Try cache first
    cached = await cache_get(cache_key)
    if cached:
        logger.info(f"Cache hit for FAERS: {drug_name}")
        return cached

    logger.info(f"Fetching FAERS data for {drug_name}")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                OPENFDA_URL,
                params={
                    "search": f"patient.drug.medicinalproduct:{drug_name}",
                    "limit": min(limit, 100),  # Cap at 100
                },
            )
            resp.raise_for_status()
            raw = resp.json()

            results = raw.get("results", [])
            events = []

            for r in results:
                try:
                    patient = r.get("patient", {})
                    drugs = patient.get("drug", [])
                    reactions = patient.get("reaction", [])

                    event_obj = {
                        "report_id": r.get("safetyreportid"),
                        "date": r.get("receiptdate"),
                        "serious": r.get("serious"),
                        "drugs": [d.get("medicinalproduct", "Unknown") for d in drugs if d.get("medicinalproduct")],
                        "reactions": [rx.get("reactionmeddrapt", "Unknown") for rx in reactions if rx.get("reactionmeddrapt")],
                        "outcomes": r.get("patient", {}).get("outcome", []),
                    }
                    events.append(event_obj)
                except Exception as e:
                    logger.warning(f"Error parsing FAERS event: {e}")
                    continue

            result = {
                "drug": drug_name,
                "total_results": raw.get("meta", {}).get("results", {}).get("total", 0),
                "returned": len(events),
                "events": events,
                "source": "FDA-FAERS (openFDA)",
            }

            # Cache for 24 hours
            await cache_set(cache_key, result, ttl=86400)
            return result

    except httpx.HTTPStatusError as e:
        logger.error(f"FAERS API HTTP error ({e.status_code}): {e}")
        return {
            "drug": drug_name,
            "total_results": 0,
            "returned": 0,
            "events": [],
            "error": f"FDA FAERS API error: {e.status_code}",
            "source": "FDA-FAERS (openFDA)",
        }
    except httpx.RequestError as e:
        logger.error(f"FAERS API request error: {e}")
        return {
            "drug": drug_name,
            "total_results": 0,
            "returned": 0,
            "events": [],
            "error": f"Network error: {str(e)}",
            "source": "FDA-FAERS (openFDA)",
        }
    except Exception as e:
        logger.error(f"Unexpected error fetching FAERS data: {e}")
        return {
            "drug": drug_name,
            "total_results": 0,
            "returned": 0,
            "events": [],
            "error": f"Unexpected error: {str(e)}",
            "source": "FDA-FAERS (openFDA)",
        }
