import httpx
import logging
from src.cache.redis_cache import cache_get, cache_set, CacheKeyBuilder
from typing import Optional

logger = logging.getLogger(__name__)

# Known DDI data (subset) for dev/testing — replace with Neo4j in production
KNOWN_INTERACTIONS = {
    ("warfarin", "aspirin"): {
        "interaction_type": "Pharmacodynamic",
        "severity": "Major",
        "description": "Aspirin increases the anticoagulant effect of warfarin, significantly raising bleeding risk.",
    },
    ("aspirin", "warfarin"): {
        "interaction_type": "Pharmacodynamic",
        "severity": "Major",
        "description": "Aspirin increases the anticoagulant effect of warfarin, significantly raising bleeding risk.",
    },
    ("metformin", "alcohol"): {
        "interaction_type": "Pharmacokinetic",
        "severity": "Moderate",
        "description": "Alcohol increases the risk of lactic acidosis with metformin.",
    },
    ("ssri", "maoi"): {
        "interaction_type": "Pharmacodynamic",
        "severity": "Contraindicated",
        "description": "Combining SSRIs with MAOIs can cause life-threatening serotonin syndrome.",
    },
    ("simvastatin", "clarithromycin"): {
        "interaction_type": "Pharmacokinetic",
        "severity": "Major",
        "description": "Clarithromycin inhibits CYP3A4, drastically increasing simvastatin levels and myopathy risk.",
    },
    ("digoxin", "amiodarone"): {
        "interaction_type": "Pharmacokinetic",
        "severity": "Major",
        "description": "Amiodarone increases digoxin plasma levels, risking toxicity.",
    },
    ("clopidogrel", "omeprazole"): {
        "interaction_type": "Pharmacokinetic",
        "severity": "Moderate",
        "description": "Omeprazole inhibits CYP2C19, reducing clopidogrel activation and antiplatelet effect.",
    },
}


async def check_drug_interaction(drug_a: str, drug_b: str) -> dict:
    """
    Check DDI between two drugs.
    Priority: Cache → Local KB → Neo4j (future) → Fallback
    """
    cache_key = CacheKeyBuilder.ddi(drug_a, drug_b)

    # Try cache first
    cached = await cache_get(cache_key)
    if cached:
        logger.info(f"Cache hit for DDI: {drug_a}+{drug_b}")
        return cached

    logger.info(f"Checking DDI for {drug_a}+{drug_b}")

    # Check local knowledge base (in-memory)
    key = (drug_a.lower(), drug_b.lower())
    key_reverse = (drug_b.lower(), drug_a.lower())
    interaction = KNOWN_INTERACTIONS.get(key) or KNOWN_INTERACTIONS.get(key_reverse)

    if interaction:
        result = {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "interaction_found": True,
            **interaction,
            "source": "local_knowledge_base",
            "severity_level": _map_severity(interaction.get("severity")),
        }
        await cache_set(cache_key, result, ttl=86400)  # Cache for 24 hours
        return result

    # TODO: Query Neo4j DDI graph for production data
    # neo4j_graph = await get_neo4j_driver()
    # result = await neo4j_graph.get_by_drug_pair(drug_a_id, drug_b_id)

    # Try DrugBank public API as fallback (if configured)
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.drugbank.com/v1/ddi",
                params={"drug_a": drug_a, "drug_b": drug_b},
                headers={"Accept": "application/json"},
            )
            if resp.status_code == 200:
                data = resp.json()
                result = {
                    "drug_a": drug_a,
                    "drug_b": drug_b,
                    "interaction_found": True,
                    **data,
                    "source": "DrugBank API",
                }
                await cache_set(cache_key, result, ttl=86400)
                return result
    except httpx.RequestError as e:
        logger.warning(f"DrugBank API error: {e}")
    except Exception as e:
        logger.warning(f"Error querying DrugBank: {e}")

    # No interaction found
    result = {
        "drug_a": drug_a,
        "drug_b": drug_b,
        "interaction_found": False,
        "interaction_type": None,
        "severity": None,
        "severity_level": 0,
        "description": f"No known interaction found between {drug_a} and {drug_b}.",
        "source": "local_knowledge_base",
    }
    await cache_set(cache_key, result, ttl=3600)  # Cache negative result for 1 hour
    return result


def _map_severity(severity_str: Optional[str]) -> int:
    """Map severity string to numeric score for sorting/filtering."""
    severity_map = {
        "contraindicated": 4,
        "major": 3,
        "moderate": 2,
        "minor": 1,
        "unknown": 0,
    }
    return severity_map.get(severity_str.lower() if severity_str else "unknown", 0)
