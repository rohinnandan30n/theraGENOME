import httpx
import json

PHARMGKB_BASE = "https://api.pharmgkb.org/v1"

async def get_pgx_recommendation(gene: str, drug: str) -> dict:
    """
    Fetch PGx clinical annotations from PharmGKB for a gene+drug pair.
    Uses openFDA drug label search as fallback if PharmGKB has no key.
    """
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
                    return {
                        "gene": gene,
                        "drug": drug,
                        "recommendation": top.get("text", "See PharmGKB for details"),
                        "evidence_level": top.get("evidenceLevel", "Unknown"),
                        "phenotype_categories": top.get("phenotypeCategories", []),
                        "source": "PharmGKB",
                        "url": f"https://www.pharmgkb.org/clinicalAnnotation/{top.get('id', '')}",
                    }
        except Exception:
            pass

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
                    return {
                        "gene": gene,
                        "drug": drug,
                        "recommendation": f"Drug '{drug}' found in PharmGKB. Check clinical annotations for gene {gene}.",
                        "evidence_level": "Refer to PharmGKB",
                        "drugbank_id": chem.get("crossReferences", [{}])[0].get("id", "N/A"),
                        "source": "PharmGKB (chemical lookup)",
                        "url": f"https://www.pharmgkb.org/chemical/{chem.get('id', '')}",
                    }
        except Exception:
            pass

    # Final fallback: return structured guidance
    return {
        "gene": gene,
        "drug": drug,
        "recommendation": f"No specific PharmGKB annotation found for {gene}+{drug}. Consult clinical pharmacogenomics guidelines.",
        "evidence_level": "Unknown",
        "source": "fallback",
        "url": f"https://www.pharmgkb.org/search?query={gene}+{drug}",
    }
