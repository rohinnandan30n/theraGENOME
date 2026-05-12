"""
TheraGenome AI — UI Adapter Layer
===================================
Transforms structured backend responses into frontend-consumable format.

Design
------
The UI adapter:
1. Accepts full backend response
2. Maps templates to UI types
3. Extracts data into components
4. Preserves multilingual compatibility (no text generation)
5. Maintains strict schema for frontend consumption

NO business logic, NO computation, ONLY transformation.
"""

from __future__ import annotations

from typing import Any

from backend.chatbot.templates import TemplateCode


# ──────────────────────────────────────────────
#  UI Type Mapping
# ──────────────────────────────────────────────

TEMPLATE_TO_UI_TYPE: dict[str, str] = {
    # Drug safety responses
    TemplateCode.DRUG_NOT_RECOMMENDED.value: "alert_card",
    TemplateCode.DRUG_USE_WITH_CAUTION.value: "alert_card",
    TemplateCode.SAFE_TO_USE.value: "success_card",
    
    # Data input acknowledgement
    TemplateCode.GENETIC_DATA_RECEIVED.value: "info_card",
    TemplateCode.INFECTION_DATA_RECEIVED.value: "info_card",
    
    # Comparison
    TemplateCode.COMPARISON_RESULT.value: "comparison_view",
    
    # Explanation
    TemplateCode.EXPLANATION_SUMMARY.value: "explanation_view",
    TemplateCode.EXPLANATION_PROVIDED.value: "explanation_view",
    
    # Report
    TemplateCode.REPORT_READY.value: "report_view",
    
    # Safety & Guardrails
    TemplateCode.SAFETY_WARNING.value: "warning_alert",
    
    # Errors & Edge Cases
    TemplateCode.INSUFFICIENT_CONTEXT.value: "warning_alert",
    TemplateCode.REQUIRE_MORE_DATA.value: "input_form",
    TemplateCode.REQUEST_MISSING_INFO.value: "input_form",
    TemplateCode.UNSUPPORTED_QUERY.value: "error_alert",
    TemplateCode.MODEL_ERROR.value: "error_alert",
    TemplateCode.GENERAL_RESPONSE.value: "generic_view",
}


class UIAdapter:
    """
    Stateless UI adapter that transforms backend responses into UI format.
    
    Thread-safe (no state mutation).
    
    Usage::
    
        adapter = UIAdapter()
        ui_response = adapter.adapt(backend_response)
    """
    
    def adapt(self, response: dict[str, Any]) -> dict[str, Any]:
        """
        Transform backend response into UI-friendly format.
        
        Parameters
        ----------
        response : dict
            Full backend response with intent, template, variables, etc.
        
        Returns
        -------
        dict
            UI adapter response with ui_type, components, metadata.
        """
        template = response.get("template", "UNKNOWN")
        ui_type = TEMPLATE_TO_UI_TYPE.get(template, "generic_view")
        
        # Build components based on response structure
        components = self._build_components(response, ui_type)
        
        # Extract metadata
        metadata = self._extract_metadata(response)
        
        return {
            "ui_type": ui_type,
            "components": components,
            "metadata": metadata,
        }
    
    def _build_components(self, response: dict[str, Any], ui_type: str) -> list[dict[str, Any]]:
        """
        Build component list based on response type and structure.
        
        Parameters
        ----------
        response : dict
            Backend response.
        ui_type : str
            UI type determined from template.
        
        Returns
        -------
        list[dict]
            List of UI components.
        """
        components = []
        
        # Add primary component based on UI type
        if ui_type == "alert_card":
            components.append(self._build_alert_card(response))
        elif ui_type == "success_card":
            components.append(self._build_success_card(response))
        elif ui_type == "info_card":
            components.append(self._build_info_card(response))
        elif ui_type == "comparison_view":
            components.extend(self._build_comparison_components(response))
        elif ui_type == "explanation_view":
            components.extend(self._build_explanation_components(response))
        elif ui_type == "report_view":
            components.extend(self._build_report_components(response))
        elif ui_type == "warning_alert":
            components.append(self._build_warning_alert(response))
        elif ui_type == "input_form":
            components.extend(self._build_input_form_components(response))
        elif ui_type == "error_alert":
            components.append(self._build_error_alert(response))
        # generic_view has no default components
        
        # Add explanation component if available (for most responses)
        if "explanation" in response and ui_type != "explanation_view":
            components.append(self._build_explanation_component(response))
        
        return components
    
    def _build_alert_card(self, response: dict[str, Any]) -> dict[str, Any]:
        """Build alert card component."""
        variables = response.get("variables", {})
        explanation = response.get("explanation", {})
        
        return {
            "type": "alert_card",
            "data": {
                "template": response.get("template"),
                "risk_level": variables.get("risk_level"),
                "reason_codes": explanation.get("reason_codes", []),
                "variables": variables,
            },
        }
    
    def _build_success_card(self, response: dict[str, Any]) -> dict[str, Any]:
        """Build success card component."""
        variables = response.get("variables", {})
        
        return {
            "type": "success_card",
            "data": {
                "template": response.get("template"),
                "risk_level": "low",
                "variables": variables,
            },
        }
    
    def _build_info_card(self, response: dict[str, Any]) -> dict[str, Any]:
        """Build info card component."""
        return {
            "type": "info_card",
            "data": {
                "template": response.get("template"),
                "variables": response.get("variables", {}),
            },
        }
    
    def _build_comparison_components(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        """Build comparison view components."""
        components = []
        
        # Comparison table
        if "comparison" in response:
            components.append({
                "type": "comparison_table",
                "data": {
                    "comparison": response["comparison"],
                    "variables": response.get("variables", {}),
                },
            })
        
        # Ranking chart
        if "ranking" in response:
            components.append({
                "type": "ranking_chart",
                "data": {
                    "ranking": response["ranking"],
                    "best_option": response.get("summary", {}).get("best_option"),
                },
            })
        
        # Summary box
        if "summary" in response:
            components.append({
                "type": "summary_box",
                "data": response["summary"],
            })
        
        return components
    
    def _build_explanation_components(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        """Build explanation view components."""
        components = []
        explanation = response.get("explanation", {})
        
        # Reason codes list
        if explanation.get("reason_codes"):
            components.append({
                "type": "reason_codes_list",
                "data": {
                    "reason_codes": explanation["reason_codes"],
                    "reason_details": explanation.get("reason_details", []),
                },
            })
        
        # Modules breakdown
        if explanation.get("modules"):
            components.append({
                "type": "modules_breakdown",
                "data": explanation["modules"],
            })
        
        return components
    
    def _build_report_components(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        """Build report view components."""
        components = []
        report = response.get("report", {})
        
        # Summary section
        if report.get("summary"):
            components.append({
                "type": "report_summary",
                "data": report["summary"],
            })
        
        # Risk analysis section
        if report.get("risk_analysis"):
            components.append({
                "type": "risk_analysis",
                "data": report["risk_analysis"],
            })
        
        # Decision factors / modules
        if report.get("decision_factors"):
            components.append({
                "type": "decision_factors",
                "data": report["decision_factors"],
            })
        
        return components
    
    def _build_warning_alert(self, response: dict[str, Any]) -> dict[str, Any]:
        """Build warning alert component."""
        return {
            "type": "warning_alert",
            "data": {
                "template": response.get("template"),
                "variables": response.get("variables", {}),
                "safety": response.get("safety"),
            },
        }
    
    def _build_input_form_components(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        """Build input form components for guidance/missing data."""
        components = []
        
        # Guidance form (for REQUEST_MISSING_INFO)
        if "guidance" in response:
            components.append({
                "type": "guidance_form",
                "data": {
                    "guidance": response["guidance"],
                    "missing_fields": response.get("variables", {}).get("missing_fields", []),
                },
            })
        
        # Error form (for REQUIRE_MORE_DATA)
        if "variables" in response and "errors" in response["variables"]:
            components.append({
                "type": "error_form",
                "data": {
                    "template": response.get("template"),
                    "errors": response["variables"]["errors"],
                    "missing_fields": response["variables"].get("missing_fields", []),
                },
            })
        
        return components
    
    def _build_error_alert(self, response: dict[str, Any]) -> dict[str, Any]:
        """Build error alert component."""
        return {
            "type": "error_alert",
            "data": {
                "template": response.get("template"),
                "variables": response.get("variables", {}),
            },
        }
    
    def _build_explanation_component(self, response: dict[str, Any]) -> dict[str, Any]:
        """Build explanation component for responses with explanation data."""
        explanation = response.get("explanation", {})
        
        return {
            "type": "explanation_detail",
            "data": {
                "reason_codes": explanation.get("reason_codes", []),
                "reason_details": explanation.get("reason_details", []),
                "modules": explanation.get("modules", {}),
            },
        }
    
    def _extract_metadata(self, response: dict[str, Any]) -> dict[str, Any]:
        """
        Extract UI-relevant metadata from backend response.
        
        Parameters
        ----------
        response : dict
            Backend response.
        
        Returns
        -------
        dict
            UI metadata (preserving multilingual info).
        """
        backend_metadata = response.get("metadata", {})
        
        return {
            "template": response.get("template"),
            "intent": response.get("intent"),
            "processing_time_ms": backend_metadata.get("processing_time_ms"),
            "intent_confidence": backend_metadata.get("intent_confidence"),
            "mode": backend_metadata.get("mode"),
        }
