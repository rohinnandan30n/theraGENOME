"""
TheraGenome AI — Intent Detection Layer
=========================================
Classifies free-text user input into a finite set of supported intents.

Strategy
--------
*   Phase 1 (current): keyword / pattern-based classifier — zero
    external dependencies, fast, deterministic.
*   Phase 2 (future):  drop-in replacement with a fine-tuned
    transformer via the same ``detect()`` interface.

Supported intents
-----------------
- input_genetic_data
- input_infection_data
- drug_analysis
- compare_drugs
- explain_result
- general_query   (fallback)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


# ──────────────────────────────────────────────
#  Intent enumeration
# ──────────────────────────────────────────────

class Intent(str, Enum):
    """Canonical intent labels used throughout the system."""
    INPUT_GENETIC_DATA  = "input_genetic_data"
    INPUT_INFECTION_DATA = "input_infection_data"
    INPUT_GUIDANCE      = "input_guidance"
    DRUG_ANALYSIS       = "drug_analysis"
    COMPARE_DRUGS       = "compare_drugs"
    EXPLAIN_RESULT      = "explain_result"
    GENERAL_QUERY       = "general_query"


# ──────────────────────────────────────────────
#  Detection result
# ──────────────────────────────────────────────

@dataclass
class IntentResult:
    """Structured output from the intent classifier."""
    intent: Intent
    confidence: float          # 0.0 – 1.0
    matched_keywords: list[str]
    raw_input: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.value,
            "confidence": round(self.confidence, 4),
            "matched_keywords": self.matched_keywords,
            "raw_input": self.raw_input,
        }


# ──────────────────────────────────────────────
#  Keyword patterns  (order matters — first match wins)
# ──────────────────────────────────────────────

_INTENT_PATTERNS: list[tuple[Intent, list[str], float]] = [
    # (intent,  keyword/regex list,  base confidence)
    (
        Intent.INPUT_GENETIC_DATA,
        [
            r"genetic\s*data",
            r"genome",
            r"genomic",
            r"dna",
            r"vcf",
            r"gene\s*variant",
            r"snp",
            r"pharmacogenom",
            r"cyp\d",
            r"hla[\s\-]?b",
            r"allele",
            r"genotype",
            r"upload.*gene",
        ],
        0.85,
    ),
    (
        Intent.INPUT_INFECTION_DATA,
        [
            r"infection",
            r"pathogen",
            r"bacteria",
            r"bacterial",
            r"virus",
            r"viral",
            r"culture\s*result",
            r"susceptibility",
            r"antibiotic\s*resist",
            r"mrsa",
            r"uti",
            r"sepsis",
            r"gram[\s\-]?(positive|negative)",
        ],
        0.85,
    ),
    (
        Intent.COMPARE_DRUGS,
        [
            r"compare",
            r"versus",
            r"\bvs\b",
            r"difference\s+between",
            r"which\s+(is\s+)?(better|safer|more\s+effective)",
            r"head[\s\-]?to[\s\-]?head",
            r"alternative",
        ],
        0.80,
    ),
    (
        Intent.DRUG_ANALYSIS,
        [
            r"drug",
            r"medication",
            r"medicine",
            r"toxicity",
            r"side\s*effect",
            r"adverse",
            r"dosage",
            r"dose",
            r"pharma",
            r"prescri",
            r"interaction",
            r"contraindic",
        ],
        0.82,
    ),
    (
        Intent.EXPLAIN_RESULT,
        [
            r"explain",
            r"why",
            r"reason",
            r"how",
            r"what\s+(does|do)\s+(this|that|it)\s+mean",
            r"interpret",
            r"clarify",
            r"break\s*down",
            r"summary",
            r"meaning\s+of",
            r"tell\s+me\s+more",
        ],
        0.78,
    ),
]


# ──────────────────────────────────────────────
#  Classifier
# ──────────────────────────────────────────────

class IntentDetector:
    """
    Rule-based intent classifier.

    Instantiate once and call :py:meth:`detect` per request.
    Thread-safe (stateless after construction).
    """

    def __init__(self) -> None:
        # Pre-compile patterns for speed.
        self._compiled: list[tuple[Intent, list[re.Pattern[str]], float]] = [
            (intent, [re.compile(p, re.IGNORECASE) for p in patterns], conf)
            for intent, patterns, conf in _INTENT_PATTERNS
        ]

    # ─── public API ───────────────────────────

    def detect(self, text: str) -> IntentResult:
        """
        Classify *text* and return a structured :class:`IntentResult`.

        The classifier iterates through intent-pattern groups in priority
        order and returns the first intent whose patterns produce at
        least one match.  Confidence is boosted by +0.03 for every
        additional keyword hit (capped at 0.99).

        Falls back to ``GENERAL_QUERY`` with confidence ``0.40`` when
        nothing matches.
        """
        if not text or not text.strip():
            return IntentResult(
                intent=Intent.GENERAL_QUERY,
                confidence=0.10,
                matched_keywords=[],
                raw_input=text or "",
            )

        normalised = text.strip().lower()

        for intent, patterns, base_conf in self._compiled:
            matched: list[str] = []
            for pat in patterns:
                if pat.search(normalised):
                    matched.append(pat.pattern)

            if matched:
                # More keyword hits → higher confidence (capped).
                bonus = min(0.14, (len(matched) - 1) * 0.03)
                confidence = min(0.99, base_conf + bonus)
                return IntentResult(
                    intent=intent,
                    confidence=confidence,
                    matched_keywords=matched,
                    raw_input=text,
                )

        # ── Fallback ──
        return IntentResult(
            intent=Intent.GENERAL_QUERY,
            confidence=0.40,
            matched_keywords=[],
            raw_input=text,
        )
