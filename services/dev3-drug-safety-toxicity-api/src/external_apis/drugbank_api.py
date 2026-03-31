import httpx

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
    Uses local knowledge base now; will query Neo4j graph in production.
    """
    key = (drug_a.lower(), drug_b.lower())
    key_reverse = (drug_b.lower(), drug_a.lower())

    interaction = KNOWN_INTERACTIONS.get(key) or KNOWN_INTERACTIONS.get(key_reverse)

    if interaction:
        return {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "interaction_found": True,
            **interaction,
            "source": "local_knowledge_base",
            "note": "Will query Neo4j DDI graph in production.",
        }

    # Try DrugBank public API as fallback
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.drugbank.com/v1/ddi",
                params={"drug_a": drug_a, "drug_b": drug_b},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass

    return {
        "drug_a": drug_a,
        "drug_b": drug_b,
        "interaction_found": False,
        "interaction_type": None,
        "severity": None,
        "description": f"No known interaction found between {drug_a} and {drug_b}.",
        "source": "local_knowledge_base",
    }
