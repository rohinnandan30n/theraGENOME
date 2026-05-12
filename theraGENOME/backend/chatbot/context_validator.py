"""
TheraGenome AI — Context Validation Layer
=========================================
Validates the context.last_response against strict Pydantic schemas.
"""

from typing import Any
from pydantic import ValidationError

from backend.chatbot.schemas import ChatbotResponse
from backend.chatbot.templates import TemplateCode, build_response

class ContextValidator:
    def validate_last_response(self, context: dict[str, Any]) -> ChatbotResponse | dict[str, Any]:
        """
        Validates `last_response` in `context`.
        Returns a validated ChatbotResponse object on success.
        Returns a failure response dictionary (INSUFFICIENT_CONTEXT) if invalid or missing.
        """
        last_response = context.get("last_response")
        
        if not last_response:
            return self._insufficient_context()

        try:
            parsed = ChatbotResponse.model_validate(last_response)
            
            if not parsed.template or not parsed.explanation.reason_codes:
                return self._insufficient_context()
                
            return parsed
        except ValidationError:
            return self._insufficient_context()

    def _insufficient_context(self) -> dict[str, Any]:
        return build_response(
            intent="explain_result",
            template=TemplateCode.INSUFFICIENT_CONTEXT,
            variables={},
            reason_codes=["INSUFFICIENT_DATA"],
            reason_details=[],
            modules={},
            metadata={"source": "explainer"}
        )
