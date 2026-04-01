"""
Medical LLM Integration Service (Task 4.5)

Handles:
- Integration with OpenAI or local Ollama (BioMistral)
- Structured prompt construction
- Narrative generation with SHAP explanations
- Streaming responses via Server-Sent Events
"""

import json
import os
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
import asyncio

from openai import AsyncOpenAI, OpenAI
import httpx

from scripts.shap_schemas import (
    VariantSHAPExplanation,
    ResistanceSHAPExplanation,
    ToxicitySHAPExplanation,
    UnifiedXAIExplanation
)
from scripts.therapy_report_schemas import TherapyDecisionReport


class LLMConfig:
    """LLM configuration management."""
    
    def __init__(self):
        # Support both OpenAI and local Ollama
        self.use_openai = os.getenv("USE_OPENAI_API", "false").lower() == "true"
        self.use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        
        # OpenAI config
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # Ollama config
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "biomistral")
        
        # Temperature & token limits
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))


class PromptTemplateBuilder:
    """Builds structured prompts for Medical LLM."""
    
    @staticmethod
    def system_prompt() -> str:
        """System prompt for clinical decision support."""
        return """You are a highly specialized Clinical Decision Support AI assistant for precision medicine and genomic medicine. 
Your role is to:
1. Analyze complex genetic, pathogen resistance, and drug toxicity data
2. Generate clinician-readable reports that explain clinical decision recommendations
3. Clearly articulate the evidence (variants, resistance markers, toxicity risks) behind each recommendation
4. Provide actionable insights for patient management
5. Always emphasize uncertainty and limitations
6. Follow Evidence-Based Medicine (EBM) principles

Guidelines:
- Write in professional medical English suitable for board-certified clinicians
- Use standardized terminology (ICD-10, SNOMED CT preferred)
- Always cite specific evidence from genetic/microbiologic data
- Highlight high-certainty findings vs. those with uncertainty
- Provide specific monitoring or follow-up recommendations
- Format output clearly with distinct sections
- Avoid over-interpretation; distinguish correlation from causation
- Always include limitations and caveats where relevant"""

    @staticmethod
    def build_variant_context(explanation: VariantSHAPExplanation) -> str:
        """Build variant explanation context."""
        context = f"""
## GENETIC RISK ANALYSIS (Dev 1 - Variant Classification)

**Classification:** {explanation.classification} (Confidence: {explanation.probability:.1%})
**Clinical Significance:** {explanation.clinical_significance}

### Top Contributing Variants (by SHAP importance):
"""
        for i, feature in enumerate(explanation.top_features[:5], 1):
            context += f"""
{i}. **{feature.feature_name}**
   - SHAP Effect: {feature.shap_value:.3f} (Impact: {feature.impact_direction})
   - Feature Value: {feature.feature_value}
   - Clinical Interpretation: {"Increases risk" if feature.impact_direction == "positive" else "Decreases risk"} of pathogenic phenotype
"""
        
        if explanation.feature_interactions:
            context += f"\n### Feature Interactions (Synergistic Effects):\n"
            for feature_pair, interaction in sorted(
                explanation.feature_interactions.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:3]:
                context += f"- {feature_pair}: {interaction:.3f}\n"
        
        context += f"\n**Model Uncertainty:** ±{explanation.uncertainty_estimate:.3f}\n"
        context += f"**SHAP Confidence:** {explanation.shap_based_confidence:.1%}\n"
        
        return context

    @staticmethod
    def build_resistance_context(explanation: ResistanceSHAPExplanation) -> str:
        """Build resistance explanation context."""
        context = f"""
## INFECTION & RESISTANCE PROFILE (Dev 2 - Pathogen Resistance)

**Organism:** {explanation.organism_name}
**Resistance Profile:** {explanation.resistance_profile_type}
**Multi-Drug Resistant:** {'Yes' if explanation.multi_drug_resistant else 'No'}

### Key Resistance Genes (by SHAP importance):
"""
        for i, gene in enumerate(explanation.contributing_genes[:5], 1):
            context += f"""
{i}. **{gene.gene_name}** (Antibiotic Class: {gene.resistance_class})
   - SHAP Contribution: {gene.shap_value:.3f}
   - Gene Present: {'Yes' if gene.gene_presence else 'No'}
   - Impact Level: {gene.impact_on_phenotype}
   - Mutation Type: {gene.mutation_type or 'N/A'}
"""
        
        context += f"\n### Predicted Antibiotic Susceptibilities:\n"
        for pheno in explanation.predicted_phenotypes[:8]:
            context += f"- **{pheno.antibiotic_name}:** {pheno.predicted_susceptibility.upper()} (Confidence: {pheno.prediction_probability:.1%})\n"
        
        context += f"\n**Model Uncertainty:** ±{explanation.uncertainty_estimate:.3f}\n"
        
        return context

    @staticmethod
    def build_toxicity_context(explanation: ToxicitySHAPExplanation) -> str:
        """Build toxicity explanation context."""
        context = f"""
## DRUG SAFETY ASSESSMENT (Dev 3 - Toxicity Prediction)

**Drug:** {explanation.drug_name}
**Overall Toxicity Risk:** {explanation.overall_toxicity_risk.upper()} (Score: {explanation.overall_risk_score:.2%})

### Organ-Specific Toxicity Assessment:
"""
        for organ_tox in explanation.organ_toxicities[:5]:
            context += f"""
**{organ_tox.organ_name.upper()}** - Risk: {organ_tox.toxicity_risk.upper()} ({organ_tox.risk_probability:.1%})
   - Top Risk Factors: {', '.join(list(organ_tox.top_risk_factors.keys())[:3])}
   - Biomarkers: {json.dumps(organ_tox.biomarker_indicators) if organ_tox.biomarker_indicators else 'Not specified'}
   - Monitoring: {'; '.join(organ_tox.monitoring_recommendations) if organ_tox.monitoring_recommendations else 'Standard monitoring'}
"""
        
        context += f"\n### Pharmacogenetics (Drug Metabolism):\n"
        context += f"- Primary Metabolizer: {explanation.metabolism_profile.primary_metabolizer}\n"
        context += f"- Metabolizer Phenotype: {explanation.metabolism_profile.metabolizer_phenotype.upper()}\n"
        context += f"- SHAP Contribution: {explanation.metabolism_profile.shap_contribution:.3f}\n"
        context += f"- Genetic Variants: {json.dumps(explanation.metabolism_profile.genetic_variants) if explanation.metabolism_profile.genetic_variants else 'None identified'}\n"
        
        if explanation.significant_interactions:
            context += f"\n### Drug-Drug Interactions:\n"
            for interaction in explanation.significant_interactions[:3]:
                context += f"- {json.dumps(interaction)}\n"
        
        if explanation.dose_adjustment_needed:
            context += f"\n### ⚠️ DOSE ADJUSTMENT REQUIRED\n"
            context += f"**Recommended Adjustment:** {explanation.recommended_dose_adjustment}\n"
        
        if explanation.absolute_contraindications:
            context += f"\n### 🚫 ABSOLUTE CONTRAINDICATIONS\n"
            for contra in explanation.absolute_contraindications:
                context += f"- {contra}\n"
        
        context += f"\n**Monitoring Plan:**\n"
        for monitoring in explanation.monitoring_plan:
            context += f"- {monitoring}\n"
        
        return context

    @staticmethod
    def build_user_message(
        report: TherapyDecisionReport,
        variant_explanation: Optional[VariantSHAPExplanation] = None,
        resistance_explanation: Optional[ResistanceSHAPExplanation] = None,
        toxicity_explanation: Optional[ToxicitySHAPExplanation] = None
    ) -> str:
        """Build complete user message with all contexts."""
        
        user_msg = f"""
# THERAPY DECISION REPORT - NARRATIVE GENERATION REQUEST

## PATIENT CONTEXT
- **Patient ID:** {report.patient_id}
- **Sample ID:** {report.sample_id}
- **Report Generated:** {report.generated_at}
- **Status:** {report.status}

## THERAPY DECISION SUMMARY
- **Recommended Drug:** {report.recommended_drug}
- **Recommendation Confidence:** {report.recommendation_confidence:.1%}
- **Alternative Drugs:** {', '.join(report.alternative_drugs) if report.alternative_drugs else 'None'}

---

"""
        
        if variant_explanation:
            user_msg += PromptTemplateBuilder.build_variant_context(variant_explanation)
            user_msg += "\n---\n"
        
        if resistance_explanation:
            user_msg += PromptTemplateBuilder.build_resistance_context(resistance_explanation)
            user_msg += "\n---\n"
        
        if toxicity_explanation:
            user_msg += PromptTemplateBuilder.build_toxicity_context(toxicity_explanation)
            user_msg += "\n---\n"
        
        user_msg += """
## NARRATIVE GENERATION REQUIREMENTS

Generate a comprehensive clinical narrative report with the following sections:

1. **PATIENT SUMMARY** (2-3 sentences)
   - Brief clinical context
   - Indication for therapy
   
2. **GENETIC RISK ANALYSIS** (if available)
   - Key genetic findings and their clinical significance
   - Pathogenic variants identified
   - Risk stratification based on genetics
   
3. **INFECTION & RESISTANCE PROFILE** (if available)
   - Pathogen identification and resistance profile
   - Relevant resistance genes present
   - Key susceptibilities and resistances
   
4. **DRUG SAFETY ASSESSMENT** (if available)
   - Organ-specific toxicity risks
   - Pharmacogenetic considerations
   - Drug-drug interactions
   - Dose adjustments if needed
   
5. **FINAL RECOMMENDATION** (1-2 paragraphs)
   - Evidence-based drug recommendation
   - Rationale considering all factors
   - Alternative options and why they were not selected
   
6. **CLINICAL MONITORING PLAN**
   - Specific monitoring parameters
   - Timeline for follow-up
   - Warning signs to watch for
   
7. **LIMITATIONS & CAVEATS**
   - Uncertainty in predictions
   - Areas requiring clinical judgment
   - Need for reference lab confirmation if applicable

---

Keep the narrative professional, evidence-based, and clinician-ready for immediate use in EHR systems.
Emphasize high-confidence findings and clearly flag areas of uncertainty.
"""
        
        return user_msg


class MedicalLLMService:
    """Service for calling Medical LLM (OpenAI or Ollama)."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._openai_client: Optional[AsyncOpenAI] = None
        self._ollama_session: Optional[httpx.AsyncClient] = None
    
    async def _get_openai_client(self) -> AsyncOpenAI:
        """Get or create OpenAI async client."""
        if self._openai_client is None:
            self._openai_client = AsyncOpenAI(
                api_key=self.config.openai_api_key,
                base_url=self.config.openai_base_url
            )
        return self._openai_client
    
    async def _get_ollama_session(self) -> httpx.AsyncClient:
        """Get or create Ollama HTTP session."""
        if self._ollama_session is None:
            self._ollama_session = httpx.AsyncClient(
                base_url=self.config.ollama_base_url,
                timeout=120.0
            )
        return self._ollama_session
    
    async def generate_narrative_stream(
        self,
        report: TherapyDecisionReport,
        variant_explanation: Optional[VariantSHAPExplanation] = None,
        resistance_explanation: Optional[ResistanceSHAPExplanation] = None,
        toxicity_explanation: Optional[ToxicitySHAPExplanation] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate narrative clinical report with streaming.
        
        Yields text chunks suitable for Server-Sent Events.
        """
        
        system_prompt = PromptTemplateBuilder.system_prompt()
        user_message = PromptTemplateBuilder.build_user_message(
            report,
            variant_explanation,
            resistance_explanation,
            toxicity_explanation
        )
        
        try:
            if self.config.use_openai and self.config.openai_api_key:
                async for chunk in await self._stream_openai(system_prompt, user_message):
                    yield chunk
            elif self.config.use_ollama:
                async for chunk in await self._stream_ollama(system_prompt, user_message):
                    yield chunk
            else:
                # Fallback: use OpenAI
                async for chunk in await self._stream_openai(system_prompt, user_message):
                    yield chunk
        
        except Exception as e:
            yield f"\n\n⚠️ **ERROR:** Failed to generate narrative: {str(e)}\n"
    
    async def _stream_openai(self, system_prompt: str, user_message: str) -> AsyncGenerator[str, None]:
        """Stream from OpenAI API."""
        client = await self._get_openai_client()
        
        stream = await client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _stream_ollama(self, system_prompt: str, user_message: str) -> AsyncGenerator[str, None]:
        """Stream from local Ollama (BioMistral)."""
        session = await self._get_ollama_session()
        
        prompt = f"""[INST] {system_prompt}

{user_message} [/INST]"""
        
        async with session.stream(
            "POST",
            "/api/generate",
            json={
                "model": self.config.ollama_model,
                "prompt": prompt,
                "stream": True,
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue
    
    async def generate_narrative_full(
        self,
        report: TherapyDecisionReport,
        variant_explanation: Optional[VariantSHAPExplanation] = None,
        resistance_explanation: Optional[ResistanceSHAPExplanation] = None,
        toxicity_explanation: Optional[ToxicitySHAPExplanation] = None,
    ) -> str:
        """Generate full narrative (non-streaming)."""
        
        full_text = ""
        async for chunk in self.generate_narrative_stream(
            report,
            variant_explanation,
            resistance_explanation,
            toxicity_explanation
        ):
            full_text += chunk
        
        return full_text
    
    async def close(self):
        """Close client connections."""
        if self._openai_client:
            await self._openai_client.close()
        if self._ollama_session:
            await self._ollama_session.aclose()
