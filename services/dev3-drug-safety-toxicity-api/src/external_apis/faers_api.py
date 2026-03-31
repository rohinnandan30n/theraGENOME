import httpx

OPENFDA_URL = "https://api.fda.gov/drug/event.json"

async def get_adverse_events(drug_name: str, limit: int = 10) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            OPENFDA_URL,
            params={
                "search": f"patient.drug.medicinalproduct:{drug_name}",
                "limit": limit
            },
        )
        resp.raise_for_status()
        raw = resp.json()

        results = raw.get("results", [])
        events = []
        for r in results:
            drugs = r.get("patient", {}).get("drug", [])
            reactions = r.get("patient", {}).get("reaction", [])
            events.append({
                "report_id": r.get("safetyreportid"),
                "date": r.get("receiptdate"),
                "serious": r.get("serious"),
                "drugs": [d.get("medicinalproduct") for d in drugs],
                "reactions": [rx.get("reactionmeddrapt") for rx in reactions],
            })

        return {
            "drug": drug_name,
            "total_results": raw.get("meta", {}).get("results", {}).get("total", 0),
            "returned": len(events),
            "events": events,
        }
