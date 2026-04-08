"""
TheraGenome AI — Explanation Engine
======================================
Provides structured explanations for past chatbot decisions by 
extracting and surfacing the modules and reason codes from the context.
"""

from typing import Any
from backend.chatbot.templates import TemplateCode, build_response

class ExplainerEngine:
    def explain(self, context: dict[str, Any], scope: str = "full") -> dict[str, Any]:
        """
        Creates an explain_result response based on the 'last_response'.
        Does NOT recompute or call external models.
        """
        last_response = context.get("last_response", {})
        explanation = last_response.get("explanation", {})
        
        modules = explanation.get("modules", {})
        if scope == "full":
            filtered_modules = modules
        else:
            filtered_modules = {}
            module_key = f"{scope}_analysis"
            if module_key in modules:
                filtered_modules[module_key] = modules[module_key]

        linked_id = last_response.get("metadata", {}).get("linked_response_id")
        meta = {"source": "explainer"}
        if linked_id:
            meta["linked_response_id"] = linked_id

        return build_response(
            intent="explain_result",
            template=TemplateCode.EXPLANATION_SUMMARY,
            variables={"scope": scope},
            reason_codes=explanation.get("reason_codes", []),
            reason_details=explanation.get("reason_details", []),
            modules=filtered_modules,
            metadata=meta
        )
