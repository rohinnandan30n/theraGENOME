"""
TheraGenome AI — Mode Filter Layer
====================================
Post-processing filter that controls the level of detail in responses
based on the user mode (``doctor`` vs ``patient``).

Design principles
-----------------
*   **No logic changes** — the filter never alters ``template``,
    ``variables``, or any clinical recommendation.
*   **Schema-preserving** — both modes return identical top-level keys.
    Patient mode only *removes* nested fields; it never renames or adds.
*   **Single responsibility** — all mode-aware data stripping happens
    here and *nowhere else* in the pipeline.

Filtering rules
---------------
- **Doctor mode**: full ``explanation.reason_codes`` + ``explanation.modules``
  (all raw model outputs, scores, technical metrics).
- **Patient mode**: keep ``explanation.reason_codes``, **remove**
  ``explanation.modules`` entirely.
"""

from __future__ import annotations

import copy
from typing import Any


# ──────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────

MODE_DOCTOR = "doctor"
MODE_PATIENT = "patient"

# Top-level keys that Patient mode is allowed to keep.
# Everything else is passed through untouched in both modes.
_EXPLANATION_KEY = "explanation"
_MODULES_KEY = "modules"


# ──────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────

class ModeFilter:
    """
    Stateless filter applied after the decision engine.

    Usage::

        filt = ModeFilter()
        filtered = filt.apply(response, mode="patient")
    """

    def apply(self, response: dict[str, Any], mode: str = MODE_DOCTOR) -> dict[str, Any]:
        """
        Filter *response* according to *mode*.

        Parameters
        ----------
        response : dict
            Full response envelope from the decision engine:
            ``{intent, template, variables, explanation, metadata}``.
        mode : str
            ``"doctor"`` — return everything.
            ``"patient"`` — strip ``explanation.modules``.

        Returns
        -------
        dict
            A **shallow copy** of the response with nested fields removed
            as needed.  The original dict is never mutated.
        """
        # Always work on a copy so upstream data stays intact.
        filtered = copy.deepcopy(response)

        # Ensure mode is recorded in metadata regardless.
        filtered.setdefault("metadata", {})["mode"] = mode

        if mode == MODE_DOCTOR:
            return filtered

        if mode == MODE_PATIENT:
            return self._filter_patient(filtered)

        # Unknown mode — default to patient (safest).
        return self._filter_patient(filtered)

    # ─── internal ─────────────────────────────

    @staticmethod
    def _filter_patient(resp: dict[str, Any]) -> dict[str, Any]:
        """
        Remove ``explanation.modules`` for patient-facing responses.

        What is preserved:
        - ``intent``
        - ``template``
        - ``variables``
        - ``explanation.reason_codes``
        - ``metadata``

        What is removed:
        - ``explanation.modules`` (all raw model outputs)
        """
        explanation = resp.get(_EXPLANATION_KEY)

        if isinstance(explanation, dict):
            # Whitelist approach: only keep explicitly allowed keys.
            allowed_keys = {"reason_codes", "reason_details"}
            
            # Rebuild explanation dict
            new_explanation = {k: v for k, v in explanation.items() if k in allowed_keys}
            resp[_EXPLANATION_KEY] = new_explanation

        return resp
