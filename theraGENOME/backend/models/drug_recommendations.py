"""
TheraGenome AI — Drug Recommendation Engine
============================================
Generates ranked, evidence-based drug recommendations for all three models:
- Genetic Model (pharmacogenomics): Drug-metabolism matching with dosing
- Resistance Model (antibiotic selection): Ranked antibiotics with resistance profiles
- Toxicity Model (drug safety): Alternative drugs with better safety profiles

Each recommendation includes:
- Ranking (1=best fit, 2=alternative, etc.)
- Specific drug name with brand names
- Initial & target dosing
- Titration schedule
- Monitoring requirements
- Expected clinical outcome
- Genetic/clinical suitability score
"""

from dataclasses import dataclass, field, asdict
from typing import Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class DrugRecommendation:
    """Structure for a single drug recommendation."""
    rank: int
    category: str
    drug_name: str
    brand_names: list[str] = field(default_factory=list)
    initial_dose: str = ""
    target_dose: str = ""
    max_dose: str = ""
    dosing_interval: str = "daily"
    titration_schedule: str = ""
    indication: str = ""
    genetic_match_score: float = 0.0  # 0.0-10.0
    genetic_reasoning: str = ""
    contraindications: list[str] = field(default_factory=list)
    precautions: list[str] = field(default_factory=list)
    monitoring_requirements: str = ""
    expected_outcome: str = ""
    onset_time: str = ""
    notes: str = ""
    interactions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ──────────────────────────────────────────────────────────────
#  GENETIC MODEL: Drug Recommendations by Metabolizer Status
# ──────────────────────────────────────────────────────────────

GENETIC_DRUG_DATABASE = {
    "poor_metabolizer": {
        "Depression/Mood": [
            {
                "rank": 1,
                "category": "Antidepressant - First Choice",
                "drug_name": "Sertraline (Zoloft)",
                "brand_names": ["Zoloft", "Lustral"],
                "initial_dose": "12.5-25mg",
                "target_dose": "50mg",
                "max_dose": "200mg",
                "titration_schedule": "Start 12.5-25mg, increase by 12.5-25mg weekly to target 50mg over 2-4 weeks",
                "genetic_match_score": 8.5,
                "genetic_reasoning": "Poor CYP2D6 metabolizers: SSRI partially cleared by CYP2D6. Start at 50% normal dose due to slower metabolism.",
                "monitoring_requirements": "Therapeutic drug monitoring at 4-6 weeks; check plasma levels weekly for first 2 weeks",
                "expected_outcome": "Symptom improvement 50-70% by week 8; higher risk of initial side effects (week 1-2)",
                "onset_time": "2-4 weeks with full effect at 8-12 weeks",
                "precautions": ["Risk of serotonin syndrome", "Hyponatremia (rare)", "GI upset first 2 weeks"],
                "interactions": ["Warfarin", "NSAIDs (GI bleeding risk)"],
            },
            {
                "rank": 2,
                "category": "Antidepressant - Alternative",
                "drug_name": "Escitalopram (Lexapro)",
                "brand_names": ["Lexapro"],
                "initial_dose": "5mg",
                "target_dose": "10mg",
                "max_dose": "20mg",
                "titration_schedule": "Start 5mg daily, increase to 10mg at week 2, then 20mg at week 4",
                "genetic_match_score": 8.0,
                "genetic_reasoning": "Moderate CYP2C19 metabolism; acceptable for poor CYP2D6 metabolizers",
                "monitoring_requirements": "Standard monitoring; therapeutic drug monitoring optional",
                "expected_outcome": "60-75% symptom improvement by week 8",
            },
            {
                "rank": 3,
                "category": "Antidepressant - Alternative",
                "drug_name": "Mirtazapine (Remeron)",
                "brand_names": ["Remeron"],
                "initial_dose": "7.5-15mg",
                "target_dose": "30mg",
                "max_dose": "45mg",
                "titration_schedule": "Start 15mg at bedtime, increase by 15mg if needed every 3-5 days",
                "genetic_match_score": 7.5,
                "genetic_reasoning": "CYP1A2/2D6/3A4 substrate; good option for poor metabolizers with CYP2D6 impairment",
                "monitoring_requirements": "Monitor for sedation, weight gain, metabolic effects",
                "expected_outcome": "Rapid onset (1-2 weeks); beneficial sedation for anxiety",
                "precautions": ["Weight gain", "Metabolic syndrome", "Sedation"],
            }
        ],
        "Hypertension": [
            {
                "rank": 1,
                "category": "Beta-Blocker - First Choice",
                "drug_name": "Atenolol (Tenormin)",
                "brand_names": ["Tenormin"],
                "initial_dose": "25mg",
                "target_dose": "50-100mg",
                "max_dose": "200mg",
                "titration_schedule": "Start 25mg daily, increase by 25-50mg every 2-4 weeks to target",
                "genetic_match_score": 9.0,
                "genetic_reasoning": "Minimal hepatic metabolism (renally eliminated); ideal for poor metabolizers",
                "monitoring_requirements": "Monitor BP weekly; check heart rate (target >50 bpm)",
                "expected_outcome": "BP reduction within 1-2 weeks; full effect at 4-6 weeks",
                "onset_time": "1-2 weeks",
            },
            {
                "rank": 2,
                "category": "ACE Inhibitor - Alternative",
                "drug_name": "Lisinopril (Prinivil)",
                "brand_names": ["Prinivil", "Zestril"],
                "initial_dose": "5-10mg",
                "target_dose": "10-20mg",
                "max_dose": "40mg",
                "genetic_match_score": 8.5,
                "genetic_reasoning": "Not metabolized hepatically; excellent for poor CYP2D6 metabolizers",
                "monitoring_requirements": "Check renal function and potassium at baseline and 2 weeks; monitor BP",
                "expected_outcome": "BP reduction over 2-4 weeks; full effect at 6-8 weeks",
                "precautions": ["Dry cough (10-20%)", "Hyperkalemia risk", "Renal impairment"],
            }
        ]
    },
    
    "intermediate_metabolizer": {
        "Depression/Mood": [
            {
                "rank": 1,
                "category": "Antidepressant - First Choice",
                "drug_name": "Sertraline (Zoloft)",
                "brand_names": ["Zoloft"],
                "initial_dose": "25mg",
                "target_dose": "50-75mg",
                "max_dose": "200mg",
                "titration_schedule": "Start 25mg daily, increase to 50mg at week 3, then 75mg at week 5",
                "genetic_match_score": 9.2,
                "genetic_reasoning": "Excellent match for intermediate metabolizers; good efficacy at lower doses",
                "monitoring_requirements": "Check plasma levels at 4-6 weeks; assess mood weekly",
                "expected_outcome": "60-70% symptom improvement by week 8",
                "onset_time": "2-4 weeks",
            },
            {
                "rank": 2,
                "category": "Antidepressant - Alternative",
                "drug_name": "Vortioxetine (Trintellix)",
                "brand_names": ["Trintellix"],
                "initial_dose": "5mg",
                "target_dose": "10-15mg",
                "max_dose": "20mg",
                "titration_schedule": "Start 5mg daily, increase to 10mg at week 2, then 15mg at week 4",
                "genetic_match_score": 8.5,
                "genetic_reasoning": "Minimal CYP2D6 involvement; even better pharmacogenomic match",
                "monitoring_requirements": "Check response at 4 weeks",
                "expected_outcome": "70-80% symptom improvement by week 8",
            }
        ],
        "Hypertension": [
            {
                "rank": 1,
                "category": "Beta-Blocker - First Choice",
                "drug_name": "Metoprolol (Lopressor)",
                "brand_names": ["Lopressor"],
                "initial_dose": "25mg",
                "target_dose": "50-100mg",
                "titration_schedule": "Start 25mg daily evening, increase by 25-50mg every 2-3 weeks",
                "genetic_match_score": 8.0,
                "genetic_reasoning": "CYP2D6 substrate; good match for intermediate metabolizers",
                "monitoring_requirements": "Monitor HR (target >50 bpm), BP response weekly",
                "expected_outcome": "BP control within 2-4 weeks",
            }
        ]
    },
    
    "normal_metabolizer": {
        "Depression/Mood": [
            {
                "rank": 1,
                "category": "Antidepressant - First Choice",
                "drug_name": "Sertraline (Zoloft)",
                "initial_dose": "50mg",
                "target_dose": "100mg",
                "max_dose": "200mg",
                "titration_schedule": "Start 50mg daily, increase to 100mg at week 3-4",
                "genetic_match_score": 9.0,
                "genetic_reasoning": "Normal metabolizer: standard dosing appropriate",
                "monitoring_requirements": "Standard monitoring; assess mood at 4, 8, 12 weeks",
                "expected_outcome": "50-70% symptom improvement by week 8",
            }
        ]
    },
    
    "ultra_rapid_metabolizer": {
        "Depression/Mood": [
            {
                "rank": 1,
                "category": "Antidepressant - First Choice",
                "drug_name": "Sertraline (Zoloft)",
                "initial_dose": "100-150mg",
                "target_dose": "150-200mg",
                "max_dose": "200mg",
                "titration_schedule": "Start 100mg daily, increase to 150mg at week 2, then 200mg at week 4",
                "genetic_match_score": 8.0,
                "genetic_reasoning": "Ultra-rapid metabolizer (CYP2D6 gene duplication): standard doses ineffective. Requires 1.5-2x normal dosing.",
                "monitoring_requirements": "TDM at 4-6 weeks; check efficacy closely",
                "expected_outcome": "May require higher than typical doses for response",
                "precautions": ["Risk of subtherapeutic levels at standard doses", "Monitor for reduced efficacy"],
            }
        ]
    }
}


def generate_genetic_drug_recommendations(
    metabolizer_status: str,
    detected_genes: list[str],
    detected_conditions: list[str] = None
) -> list[dict[str, Any]]:
    """
    Generate ranked drug recommendations based on metabolizer status and detected genetic variants.
    
    Parameters
    ----------
    metabolizer_status : str
        One of: "poor_metabolizer", "intermediate_metabolizer", "normal_metabolizer", "ultra_rapid_metabolizer"
    detected_genes : list[str]
        List of detected genes (e.g., ["CYP2D6", "CYP2C19"])
    detected_conditions : list[str]
        Patient conditions (e.g., ["Depression", "Hypertension"]) to guide recommendations
    
    Returns
    -------
    list[dict[str, Any]]
        Ranked list of drug recommendations
    """
    detected_conditions = detected_conditions or []
    recommendations = []
    
    # Get base recommendations for metabolizer status
    status_drugs = GENETIC_DRUG_DATABASE.get(metabolizer_status, {})
    
    # Get condition-specific recommendations
    for condition in detected_conditions:
        condition_drugs = status_drugs.get(condition, []) or status_drugs.get("Depression/Mood", [])
        recommendations.extend(condition_drugs)
    
    # If no conditions specified, return general antidepressant options
    if not recommendations:
        recommendations = status_drugs.get("Depression/Mood", []) or list(status_drugs.values())[0]
    
    # Sort by rank
    recommendations.sort(key=lambda x: x.get("rank", 999))
    
    logger.info(f"✅ Generated {len(recommendations)} drug recommendations for {metabolizer_status}")
    return recommendations


# ──────────────────────────────────────────────────────────────
#  RESISTANCE MODEL: Antibiotic Recommendations by Pathogen
# ──────────────────────────────────────────────────────────────

ANTIBIOTIC_DATABASE = {
    "MRSA": [
        {
            "rank": 1,
            "drug_name": "Vancomycin IV",
            "category": "Glycopeptide",
            "initial_dose": "15-20 mg/kg IV Q8-12H",
            "target_dose": "15-20 mg/kg Q8-12H",
            "indication": "Serious MRSA infections (bloodstream, pneumonia, endocarditis)",
            "suitability_score": 9.5,
            "reasoning": "Gold standard for severe MRSA. Requires TDM (target trough 15-20 mcg/mL).",
            "monitoring": "Renal function, hearing baseline; vancomycin levels (trough); nephrotoxicity risk",
            "monitoring_interval": "Day 3-5 for TDM; weekly renal function",
            "expected_onset": "Gradual (5-7 days for clinical response)",
            "precautions": ["Red man syndrome", "Nephrotoxicity", "Ototoxicity"],
        },
        {
            "rank": 2,
            "drug_name": "Daptomycin IV",
            "category": "Cyclic lipopeptide",
            "initial_dose": "6 mg/kg IV Q24H",
            "target_dose": "6-10 mg/kg IV daily",
            "indication": "Skin/soft tissue MRSA infections, bloodstream infections (non-pneumonia)",
            "suitability_score": 8.5,
            "reasoning": "Good for endocarditis and bacteremia. NOT for pneumonia (inactivated by lung surfactant).",
            "monitoring": "Renal function, CK levels (myopathy risk)",
            "expected_onset": "2-3 days for clinical response",
            "precautions": ["Muscle toxicity (high CK)", "CNS effects", "Avoid in pneumonia"],
        },
        {
            "rank": 3,
            "drug_name": "Linezolid PO/IV",
            "category": "Oxazolidinone",
            "initial_dose": "600mg Q12H",
            "target_dose": "600mg Q12H",
            "indication": "Mild-moderate MRSA infections, skin/soft tissue, or oral step-down",
            "suitability_score": 8.0,
            "reasoning": "Good oral bioavailability. 100% bioavailability PO vs IV (bridge possible).",
            "monitoring": "CBC weekly (thrombocytopenia risk), neuropathy symptoms",
            "expected_onset": "2-4 days",
            "precautions": ["Thrombocytopenia", "Peripheral neuropathy", "Serotonin syndrome (SSRIs)"],
        }
    ],
    
    "Pseudomonas aeruginosa": [
        {
            "rank": 1,
            "drug_name": "Piperacillin-tazobactam IV",
            "category": "Beta-lactam/Beta-lactamase inhibitor",
            "initial_dose": "3.375g Q4-6H or 4.5g Q6-8H",
            "target_dose": "4.5g Q6H",
            "indication": "Pseudomonas aeruginosa pneumonia, UTI, bloodstream infections",
            "suitability_score": 9.0,
            "reasoning": "First-line for empiric Pseudomonas coverage. Good lung penetration.",
            "monitoring": "Renal function, allergy history",
            "expected_onset": "1-2 days for clinical response",
            "precautions": ["Penicillin cross-reactivity (~1%)", "Diarrhea (C. diff risk)"],
        },
        {
            "rank": 2,
            "drug_name": "Ciprofloxacin IV/PO",
            "category": "Fluoroquinolone",
            "initial_dose": "400mg IV Q12H or 750mg PO Q12H",
            "target_dose": "750mg Q12H",
            "indication": "Pseudomonas UTI, respiratory tract, skin infections",
            "suitability_score": 7.5,
            "reasoning": "Good bioavailability; oral option available. High Pseudomonas coverage.",
            "monitoring": "Tendon integrity, QT interval (elderly)",
            "expected_onset": "2-3 days",
            "precautions": ["Tendinopathy", "QT prolongation", "Photosensitivity"],
        }
    ],
    
    "E. coli (ESBL)": [
        {
            "rank": 1,
            "drug_name": "Carbapenem (Meropenem/Ertapenem) IV",
            "category": "Carbapenem",
            "initial_dose": "1g Q8H (meropenem) or 1g Q24H (ertapenem)",
            "target_dose": "1g Q8H",
            "indication": "ESBL E. coli with serious infections (bacteremia, pneumonia, intra-abdominal)",
            "suitability_score": 9.5,
            "reasoning": "Gold standard for ESBL-producing organisms. Broad spectrum, resistant to ESBLs.",
            "monitoring": "Renal function, seizure risk (high doses), allergy history",
            "expected_onset": "1-2 days",
            "precautions": ["Cross-reactivity with penicillins (~1-3%)", "Seizures (high doses, renal impairment)"],
        },
        {
            "rank": 2,
            "drug_name": "Cefepime IV",
            "category": "4th generation cephalosporin",
            "initial_dose": "2g Q12H",
            "target_dose": "2g Q8H",
            "indication": "ESBL E. coli with moderate infections; can be used if susceptible",
            "suitability_score": 7.0,
            "reasoning": "Some coverage of ESBLs; less reliable than carbapenems.",
            "monitoring": "Allergy history, CNS effects",
            "precautions": ["Variable ESBL coverage (not reliable)", "CNS toxicity"],
        }
    ]
}


def generate_antibiotic_recommendations(
    pathogen: str,
    infection_site: str = "bloodstream",
    severity: str = "serious"
) -> list[dict[str, Any]]:
    """
    Generate ranked antibiotic recommendations based on pathogen and clinical context.
    
    Parameters
    ----------
    pathogen : str
        Detected organism (e.g., "MRSA", "Pseudomonas aeruginosa", "E. coli")
    infection_site : str
        Location of infection (e.g., "bloodstream", "lung", "urinary", "wound")
    severity : str
        Severity level ("mild", "moderate", "serious", "critical")
    
    Returns
    -------
    list[dict[str, Any]]
        Ranked list of antibiotic recommendations
    """
    recommendations = ANTIBIOTIC_DATABASE.get(pathogen, [])
    
    if not recommendations:
        logger.warning(f"⚠️ No specific recommendations for {pathogen}; returning default broad-spectrum")
        recommendations = [{
            "rank": 1,
            "drug_name": "Broad-spectrum beta-lactam (Pending culture results)",
            "suitability_score": 5.0,
            "reasoning": "Empiric coverage pending culture identification",
        }]
    
    logger.info(f"✅ Generated {len(recommendations)} antibiotic recommendations for {pathogen}")
    return recommendations


# ──────────────────────────────────────────────────────────────
#  TOXICITY MODEL: Safer Drug Alternatives
# ──────────────────────────────────────────────────────────────

SAFER_ALTERNATIVES = {
    "warfarin": [
        {
            "rank": 1,
            "safer_drug": "Apixaban (Eliquat)",
            "reason": "DOAC; no monitoring required, predictable PK, fewer interactions",
            "indication": "Atrial fibrillation, VTE prophylaxis",
            "suitability_score": 9.0,
        }
    ],
    "NSAIDs": [
        {
            "rank": 1,
            "safer_drug": "Acetaminophen (Tylenol)",
            "reason": "Lower GI bleed risk, less renal toxicity",
            "indication": "Pain, fever",
            "suitability_score": 8.5,
        },
        {
            "rank": 2,
            "safer_drug": "Topical NSAIDs (Diclofenac gel)",
            "reason": "Local therapy, minimal systemic absorption",
            "indication": "Musculoskeletal pain, arthritis",
            "suitability_score": 8.0,
        }
    ],
    "metformin": [
        {
            "rank": 1,
            "safer_drug": "GLP-1 agonists (Semaglutide)",
            "reason": "Lower hypoglycemia risk, weight loss benefit, cardioprotection",
            "indication": "Type 2 diabetes with cardiovascular disease",
            "suitability_score": 8.0,
        }
    ]
}


def generate_safer_alternatives(
    original_drug: str,
    contraindication_reason: str = ""
) -> list[dict[str, Any]]:
    """
    Generate safer drug alternatives when toxicity or contraindications are detected.
    
    Parameters
    ----------
    original_drug : str
        Original drug showing toxicity/contraindication risk
    contraindication_reason : str
        Reason for seeking alternative (e.g., "renal impairment", "liver disease")
    
    Returns
    -------
    list[dict[str, Any]]
        Ranked list of safer alternative drugs
    """
    alternatives = SAFER_ALTERNATIVES.get(original_drug.lower(), [])
    
    if alternatives:
        logger.info(f"✅ Found {len(alternatives)} safer alternatives to {original_drug}")
    else:
        logger.warning(f"⚠️ No pre-defined alternatives for {original_drug}")
        alternatives = [{
            "rank": 1,
            "safer_drug": "Consult pharmacist for safer alternative",
            "reason": f"Toxicity risk due to: {contraindication_reason}",
            "suitability_score": 5.0,
        }]
    
    return alternatives
