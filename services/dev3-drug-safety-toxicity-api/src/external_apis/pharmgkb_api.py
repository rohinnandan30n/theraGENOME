import httpx
import json
import logging
from src.cache.redis_cache import cache_get, cache_set, CacheKeyBuilder
from src.config import settings

logger = logging.getLogger(__name__)

PHARMGKB_BASE = "https://api.pharmgkb.org/v1"


async def get_pgx_recommendation(gene: str, drug: str) -> dict:
    """
    Fetch PGx clinical annotations from PharmGKB for a gene+drug pair.
    Caches results. Uses fallbacks for missing data.
    """
    cache_key = CacheKeyBuilder.pgx_recommendation(gene, drug)

    # Try cache first
    cached = await cache_get(cache_key)
    if cached:
        logger.info(f"Cache hit for PGx: {gene}+{drug}")
        return cached

    logger.info(f"Fetching PGx data for {gene}+{drug} from PharmGKB")

    # Try PharmGKB public API (no key needed for basic lookups)
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{PHARMGKB_BASE}/clinicalAnnotation",
                params={"gene": gene, "drug": drug, "view": "base"},
            )
            if resp.status_code == 200:
                data = resp.json()
                annotations = data.get("data", [])
                if annotations:
                    top = annotations[0]
                    result = {
                        "gene": gene,
                        "drug": drug,
                        "recommendation": top.get("text", "See PharmGKB for details"),
                        "evidence_level": top.get("evidenceLevel", "Unknown"),
                        "phenotype_categories": top.get("phenotypeCategories", []),
                        "implication": top.get("implications", None),
                        "dosing_guidance": top.get("dosingGuideline", None),
                        "source": "PharmGKB",
                        "url": f"https://www.pharmgkb.org/clinicalAnnotation/{top.get('id', '')}",
                    }
                    await cache_set(cache_key, result, ttl=86400)  # Cache for 24 hours
                    return result
        except httpx.RequestError as e:
            logger.warning(f"PharmGKB API error: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error querying PharmGKB: {e}")

    # Fallback: search PharmGKB chemical + gene pages
    try:
        resp = await client.get(
            f"{PHARMGKB_BASE}/chemical",
            params={"name": drug, "view": "base"},
        )
        if resp.status_code == 200:
            chemicals = resp.json().get("data", [])
            if chemicals:
                chem = chemicals[0]
                result = {
                    "gene": gene,
                    "drug": drug,
                    "recommendation": f"Drug '{drug}' found in PharmGKB. Check clinical annotations for gene {gene}.",
                    "evidence_level": "Refer to PharmGKB",
                    "source": "PharmGKB (chemical lookup)",
                    "url": f"https://www.pharmgkb.org/chemical/{chem.get('id', '')}",
                }
                await cache_set(cache_key, result, ttl=86400)
                return result
    except Exception as e:
        logger.warning(f"PharmGKB chemical lookup error: {e}")

    # Final fallback: return structured guidance (cache this too as negative)
    result = {
        "gene": gene,
        "drug": drug,
        "recommendation": f"No specific PharmGKB annotation found for {gene}+{drug}. Consult clinical pharmacogenomics guidelines.",
        "evidence_level": "Unknown",
        "source": "fallback",
        "url": f"https://www.pharmgkb.org/search?query={gene}+{drug}",
    }
    await cache_set(cache_key, result, ttl=3600)  # Cache fallback for 1 hour only
    return result
