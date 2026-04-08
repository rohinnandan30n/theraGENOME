"""
TheraGenome AI — Application Entry Point
==========================================
FastAPI application factory.  Run with::

    uvicorn backend.main:app --reload --port 8000

Or without FastAPI::

    python -m backend.main
"""

from __future__ import annotations

import json
import sys

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from backend.chatbot.controller import api_router
    from backend.chatbot.demo_api import demo_router

    app = FastAPI(
        title="TheraGenome AI",
        version="0.1.0",
        description=(
            "Healthcare AI chatbot engine — intent detection, "
            "model routing, and structured clinical decision responses."
        ),
    )

    # CORS — tighten origins in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if api_router is not None:
        app.include_router(api_router)

    if demo_router is not None:
        app.include_router(demo_router)

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "theragenome-ai"}

except ImportError:
    app = None  # type: ignore[assignment]


# ──────────────────────────────────────────────
#  CLI fallback (no FastAPI required)
# ──────────────────────────────────────────────

def _cli_demo() -> None:
    """Quick smoke test via the command line."""
    from backend.chatbot.controller import process_query

    queries = [
        ("Analyse the toxicity of amoxicillin", "doctor", {"drug": "amoxicillin"}),
        ("Compare penicillin vs vancomycin", "patient", {"drugs": ["penicillin", "vancomycin"]}),
        ("Upload my genetic data", "doctor", {"genetic_data": {"markers": ["CYP2D6"]}}),
    ]

    for text, mode, ctx in queries:
        print(f"\n{'='*60}")
        print(f"INPUT : {text}")
        print(f"MODE  : {mode}")
        result = process_query(text, mode=mode, context=ctx)
        print(json.dumps(result, indent=2))

    print(f"\n{'='*60}")
    print("CLI demo complete.")


if __name__ == "__main__":
    if app is not None and "--serve" in sys.argv:
        import uvicorn
        uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        _cli_demo()
