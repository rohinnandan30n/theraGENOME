"""
TheraGenome AI — Pydantic Schemas
==================================
Strict validation models for internal contexts and external API boundaries.
"""

from typing import Any
from pydantic import BaseModel, Field

class ReasonDetail(BaseModel):
    code: str
    module: str
    severity: str

class ExplanationData(BaseModel):
    reason_codes: list[str] = Field(default_factory=list)
    reason_details: list[ReasonDetail] = Field(default_factory=list)
    modules: dict[str, Any] = Field(default_factory=dict)

class ChatbotResponse(BaseModel):
    intent: str
    template: str
    variables: dict[str, Any]
    explanation: ExplanationData
    metadata: dict[str, Any]
