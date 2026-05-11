"""
TheraGenome AI — Report Generation Engine
===========================================
Transforms the latest system output into a structured report object.

Design
------
The report engine:
1. Takes the latest decision/explanation (last_response)
2. Extracts key data points
3. Formats them into a structured report
4. Returns export-ready JSON

NO computation, NO model calls, ONLY transformation.
"""

from __future__ import annotations

from typing import Any

from backend.chatbot.templates import TemplateCode


class ReportEngine:
    """
    Stateless report generation engine.
    
    Transforms a last_response into a structured report object
    suitable for export and analysis.
    
    Usage::
    
        report_engine = ReportEngine()
        report = report_engine.generate(context={"last_response": response})
    """
    
    def generate(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a structured report from the latest system output.
        
        Parameters
        ----------
        context : dict
            Must contain "last_response" key with previous response.
        
        Returns
        -------
        dict
            Structured report envelope with REPORT_READY or INSUFFICIENT_CONTEXT template.
        """
        last_response = context.get("last_response")
        
        # Handle missing context
        if not last_response:
            return {
                "intent": "generate_report",
                "template": TemplateCode.INSUFFICIENT_CONTEXT.value,
                "variables": {},
                "explanation": {
                    "reason_codes": ["MISSING_RESPONSE"],
                    "reason_details": [],
                },
                "metadata": {
                    "source": "report_engine",
                },
            }
        
        # Extract data from last_response
        variables = last_response.get("variables", {})
        explanation = last_response.get("explanation", {})
        
        # Build report structure
        report = self._build_report(variables, explanation)
        
        return {
            "intent": "generate_report",
            "template": TemplateCode.REPORT_READY.value,
            "report": report,
            "metadata": {
                "source": "report_engine",
            },
        }
    
    def _build_report(
        self, variables: dict[str, Any], explanation: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Build the report structure from extracted data.
        
        Parameters
        ----------
        variables : dict
            Variables from the decision template.
        explanation : dict
            Explanation data from the decision.
        
        Returns
        -------
        dict
            Structured report with summary, risk_analysis, and decision_factors.
        """
        # Extract summary data
        recommended_option = variables.get("recommended_option")
        confidence = variables.get("confidence_score", variables.get("confidence"))
        
        # Extract risk analysis data
        risk_level = self._extract_risk_level(variables, explanation)
        reason_codes = explanation.get("reason_codes", [])
        
        # Extract decision factors
        modules = explanation.get("modules", {})
        
        return {
            "summary": {
                "recommended_option": recommended_option,
                "confidence": confidence,
            },
            "risk_analysis": {
                "risk_level": risk_level,
                "reason_codes": reason_codes,
            },
            "decision_factors": {
                "modules": modules,
            },
        }
    
    def _extract_risk_level(
        self, variables: dict[str, Any], explanation: dict[str, Any]
    ) -> str | None:
        """
        Extract risk level from variables or explanation.
        
        Parameters
        ----------
        variables : dict
            Variables dict from decision.
        explanation : dict
            Explanation dict from decision.
        
        Returns
        -------
        str | None
            Risk level (low, medium, high) or None if not found.
        """
        # Try to get risk_level from variables
        if "risk_level" in variables:
            return variables["risk_level"]
        
        # Try to extract from explanation reason_codes
        reason_codes = explanation.get("reason_codes", [])
        if any("high" in code.lower() for code in reason_codes):
            return "high"
        if any("medium" in code.lower() for code in reason_codes):
            return "medium"
        if any("low" in code.lower() for code in reason_codes):
            return "low"
        
        # Try to extract from modules (toxicity analysis)
        modules = explanation.get("modules", {})
        if "toxicity_analysis" in modules:
            toxicity_score = modules["toxicity_analysis"].get("score")
            if toxicity_score and isinstance(toxicity_score, (int, float)):
                if toxicity_score >= 0.7:
                    return "high"
                elif toxicity_score >= 0.4:
                    return "medium"
                else:
                    return "low"
        
        return None
