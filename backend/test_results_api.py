"""
Test Results API Router
"""
from fastapi import APIRouter

test_results_router = APIRouter(prefix="/api/v1", tags=["test-results"])

@test_results_router.get("/test-results")
async def get_test_results():
    """
    Returns Emily Rodriguez's clinical pharmacogenomics report from patient_report_emily.txt
    Patient ID: PAT-002-2026 | Age: 47 | Female | Hispanic/Latin American
    """
    return {
        "status": "success",
        "summary": "CLINICAL PHARMACOGENOMICS REPORT\n\nPatient: Emily Rodriguez (PAT-002-2026)\nAge: 47 years | Female | Hispanic/Latin American\nSequencing Type: Whole Exome Sequencing (WXS)\nLaboratory: Advanced Genetic Diagnostics Inc.\nReport Date: May 10, 2026\nCertified By: Dr. Michael Chen, MD, PhD - Clinical Genetics\nCLIA: 12D2159588\n\nOVERALL RISK LEVEL: MODERATE-HIGH\nCancer Predisposition: HIGH (BRCA2 + CHEK2 mutations)\nMetabolizer Status: Rapid CYP2D6, Rapid NAT2 Acetylator\nMajor Alerts: 2 (Irinotecan contraindication, Cancer predisposition)\nDrug-Gene Interactions: 8\nDisease Risk Variants: 2 (BRCA2, CHEK2)",
        "data": {
            "test_counts": {
                "normal": 5,
                "abnormal": 5,
                "critical": 4
            },
            "tests": [
                {
                    "test_name": "CYP2D6 - Rapid Metabolizer",
                    "abnormality": "critical",
                    "value": "*1/*1xN (3 gene copies)",
                    "unit": "Duplication",
                    "reference_range": "2 copies (normal)"
                },
                {
                    "test_name": "CYP2C19 - Normal Metabolizer",
                    "abnormality": "normal",
                    "value": "*1/*1",
                    "unit": "rs4244285",
                    "reference_range": "Normal drug clearance"
                },
                {
                    "test_name": "CYP2C9 - Normal Metabolizer",
                    "abnormality": "normal",
                    "value": "*1/*1",
                    "unit": "rs1057910",
                    "reference_range": "Normal warfarin metabolism"
                },
                {
                    "test_name": "CYP3A4/5 - Normal Activity",
                    "abnormality": "normal",
                    "value": "Wild-type",
                    "unit": "None detected",
                    "reference_range": "Normal metabolism"
                },
                {
                    "test_name": "TPMT - Normal Activity",
                    "abnormality": "normal",
                    "value": "*1/*1",
                    "unit": "rs1142345",
                    "reference_range": "Normal thiopurine metabolism"
                },
                {
                    "test_name": "NAT2 - Rapid Acetylator",
                    "abnormality": "abnormal",
                    "value": "*4/*4",
                    "unit": "rs1801280",
                    "reference_range": "Normal acetylator"
                },
                {
                    "test_name": "SLCO1B1 - Reduced Function",
                    "abnormality": "abnormal",
                    "value": "*5/*1",
                    "unit": "rs6917289",
                    "reference_range": "Normal statin metabolism"
                },
                {
                    "test_name": "UGT1A1 - Gilbert Syndrome",
                    "abnormality": "critical",
                    "value": "TA7/TA7",
                    "unit": "rs8175347 - Reduced bilirubin conjugation",
                    "reference_range": "TA6/TA6 (normal)"
                },
                {
                    "test_name": "HLA-A - Normal",
                    "abnormality": "normal",
                    "value": "HLA-A*02:01",
                    "unit": "No contraindications",
                    "reference_range": "Normal"
                },
                {
                    "test_name": "BRCA2 - Heterozygous Carrier",
                    "abnormality": "critical",
                    "value": "c.9097C>T (p.Arg3033Ter)",
                    "unit": "rs80202993 - PATHOGENIC",
                    "reference_range": "Wild-type"
                },
                {
                    "test_name": "CHEK2 - Heterozygous Carrier",
                    "abnormality": "critical",
                    "value": "1100delC (c.1100delC)",
                    "unit": "rs555607708 - PATHOGENIC",
                    "reference_range": "Wild-type"
                },
                {
                    "test_name": "PTEN - Normal",
                    "abnormality": "normal",
                    "value": "Wild-type",
                    "unit": "None detected",
                    "reference_range": "No Cowden syndrome risk"
                },
                {
                    "test_name": "TP53 - Normal",
                    "abnormality": "normal",
                    "value": "Wild-type",
                    "unit": "None detected",
                    "reference_range": "No p53 predisposition"
                }
            ],
            "analysis": {
                "critical_findings": [
                    {
                        "test": "BRCA2 Mutation - CRITICAL",
                        "value": "c.9097C>T",
                        "unit": "p.Arg3033Ter (Heterozygous)",
                        "reference": "Wild-type / Normal",
                        "deviation_percent": 100
                    },
                    {
                        "test": "UGT1A1 Gilbert Syndrome - CRITICAL",
                        "value": "TA7/TA7",
                        "unit": "Reduced bilirubin conjugation",
                        "reference": "TA6/TA6 (normal)",
                        "deviation_percent": 100
                    },
                    {
                        "test": "CYP2D6 Gene Duplication - CRITICAL",
                        "value": "3 gene copies",
                        "unit": "Rapid metabolizer phenotype",
                        "reference": "2 copies (normal)",
                        "deviation_percent": 50
                    },
                    {
                        "test": "CHEK2 Mutation - CRITICAL",
                        "value": "1100delC",
                        "unit": "Heterozygous deletion (Pathogenic)",
                        "reference": "Wild-type / Normal",
                        "deviation_percent": 100
                    }
                ],
                "drug_recommendations": [
                    {
                        "disease": "Pharmacogenomics",
                        "drug": "Tramadol or Codeine",
                        "class": "Analgesic",
                        "dosage": "150-200mg daily (INCREASED from standard 50-100mg)",
                        "note": "Rapid CYP2D6 metabolizer with gene duplication (3 copies) - standard doses may be ineffective. May need 150-200% of normal doses. Monitor pain control at each visit."
                    },
                    {
                        "disease": "Pharmacogenomics",
                        "drug": "Sulfamethoxazole",
                        "class": "Antibiotic",
                        "dosage": "800-1000mg twice daily",
                        "note": "Rapid NAT2 acetylator - standard dosing appropriate. Fast drug clearance for acetylated drugs. Monitor for rash, fever, joint pain."
                    },
                    {
                        "disease": "Pharmacogenomics",
                        "drug": "Atorvastatin",
                        "class": "Statin (Cholesterol)",
                        "dosage": "10-20mg daily (CONSERVATIVE START)",
                        "note": "SLCO1B1*5 - reduced statin metabolism. Start low, titrate slowly. Check lipid panel in 6 weeks. Consider pravastatin as alternative."
                    },
                    {
                        "disease": "Pharmacogenomics",
                        "drug": "Irinotecan",
                        "class": "Chemotherapy",
                        "dosage": "NOT RECOMMENDED or 75% dose reduction ONLY",
                        "note": "🛑 CRITICAL - UGT1A1 Gilbert Syndrome (TA7/TA7) HIGH TOXICITY RISK. If cancer treatment needed, use alternative chemotherapy. If irinotecan unavoidable, reduce to 75% dose with close monitoring of bilirubin, CBC for neutropenia and diarrhea."
                    },
                    {
                        "disease": "Pharmacogenomics",
                        "drug": "Tamoxifen",
                        "class": "Hormonal therapy",
                        "dosage": "20mg daily (with monitoring)",
                        "note": "Rapid CYP2D6 metabolizer - converted by CYP2D6 to active metabolites. Therapeutic drug level may be suboptimal. Consider alternative or combination therapy. Monitor efficacy closely."
                    }
                ]
            }
        },
        "recommendations": [
            "🔴 URGENT: Genetic counseling ESSENTIAL - Discuss BRCA2 and CHEK2 mutations implications, family screening recommendations, surveillance vs preventive surgery options",
            "🔴 BRCA2 CANCER RISK: Breast cancer 45-87% by age 70 | Ovarian cancer 11-40% | Pancreatic cancer 5-10%",
            "🔴 CHEK2 CANCER RISK: Approximately 2-3x general population risk | Combined with BRCA2 increases overall cancer predisposition significantly",
            "🔴 PHARMACOTHERAPY ALERT: Rapid CYP2D6 metabolizer status (gene duplication) - standard pain medication may be ineffective, assess need for higher doses",
            "⚠️ IRINOTECAN CONTRAINDICATION: UGT1A1 Gilbert Syndrome - high severe toxicity risk (neutropenia, diarrhea requiring hospitalization)",
            "⚠️ STATIN DOSING: SLCO1B1 reduced function - start conservative doses, monitor for muscle pain/weakness, consider pravastatin alternative",
            "✓ Oncology consultation: Enhanced cancer screening protocols, family history assessment, chemotherapy planning for UGT1A1 deficiency",
            "✓ Pharmacist consultation: Review current medications against rapid metabolizer status, assess pain control adequacy, evaluate drug interactions",
            "✓ Gynecology consultation: Annual mammography + MRI, ovarian ultrasound surveillance, discuss risk-reducing mastectomy/salpingo-oophorectomy",
            "✓ Lifestyle: Exercise 150min/week, high-fiber diet, avoid tobacco, maintain healthy BMI, stress management - cancer risk reduction strategies"
        ]
    }
