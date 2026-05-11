from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import psycopg2
import json
from datetime import datetime
import os
import sys

# Import routers from main app
try:
    from backend.auth_api import auth_router
    from backend.chatbot.controller import api_router
    from backend.chatbot.demo_api import demo_router
    from backend.chatbot.report_api import report_router
except ImportError:
    auth_router = None
    api_router = None
    demo_router = None
    report_router = None

app = FastAPI(title="TheraGenome Hackathon", version="1.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8001", "http://127.0.0.1:8001", "http://localhost", "http://127.0.0.1", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth and chatbot routers
if auth_router:
    app.include_router(auth_router)
if api_router:
    app.include_router(api_router)
if demo_router:
    app.include_router(demo_router)
if report_router:
    app.include_router(report_router)

# In-memory database mock (for demo/testing without PostgreSQL)
MOCK_DATABASE = {
    "variants": [],
    "audit_logs": []
}

# Database connection
def get_db():
    # Return mock database for hackathon demo
    return MOCK_DATABASE

# ============================================
# ENDPOINT 1: Health Check
# ============================================
@app.get("/health")
async def health():
    """Kubernetes health probe endpoint"""
    return {
        "status": "healthy",
        "app": "TheraGenome",
        "version": "1.0-hackathon",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================
# ENDPOINT 2: Upload & Classify Variants
# ============================================
@app.post("/api/v1/classify")
async def classify_variants(file: UploadFile = File(...)):
    """
    Accept JSON variant file
    Process variants through classification pipeline
    Return results + drug interactions
    """
    try:
        # Read uploaded file
        contents = await file.read()
        variants = json.loads(contents)
        
        results = []
        db = get_db()
        
        for variant in variants:
            gene = variant.get("gene", "UNKNOWN")
            mutation = variant.get("mutation", "p.R175H")
            
            # Simplified classification logic
            if "frameshift" in mutation.lower() or "nonsense" in mutation.lower():
                classification = "PATHOGENIC"
                acmg_score = 0.95
            elif "missense" in mutation.lower():
                classification = "VUS"  # Variant of Uncertain Significance
                acmg_score = 0.60
            else:
                classification = "BENIGN"
                acmg_score = 0.15
            
            # Look up drug interactions
            drugs = DRUG_DATABASE.get(gene.upper(), [])
            
            # Auto-recommend drugs based on classification
            recommended_drugs = []
            if classification == "PATHOGENIC" and drugs:
                # For pathogenic variants, recommend all available drugs
                recommended_drugs = drugs
            elif classification == "VUS" and drugs:
                # For VUS, suggest drugs but mark for review
                recommended_drugs = [{"review_required": True, **drug} for drug in drugs]
            
            result = {
                "gene": gene,
                "mutation": mutation,
                "classification": classification,
                "acmg_score": acmg_score,
                "drug_interactions": drugs,
                "recommended_drugs": recommended_drugs,
                "recommendation_status": "approved" if classification == "PATHOGENIC" else "review_pending" if classification == "VUS" else "not_needed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in mock database
            db["variants"].append({
                "gene": gene,
                "mutation": mutation,
                "classification": classification,
                "details": result,
                "created_at": datetime.utcnow().isoformat()
            })
            
            # Log for audit trail (HIPAA requirement)
            db["audit_logs"].append({
                "action": "VARIANT_CLASSIFIED",
                "resource": f"{gene}:{mutation}",
                "user_id": "hackathon_user",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            results.append(result)
        
        return {
            "status": "success",
            "variants_processed": len(results),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )

# ============================================
# ENDPOINT 3: Get Results (for dashboard)
# ============================================
@app.get("/api/v1/results")
async def get_results(limit: int = 10):
    """Fetch recent classification results for dashboard"""
    db = get_db()
    
    # Get last 'limit' results
    results = []
    for variant in db["variants"][-limit:]:
        results.append({
            "gene": variant["gene"],
            "mutation": variant["mutation"],
            "classification": variant["classification"],
            "details": variant["details"],
            "created_at": variant["created_at"]
        })
    
    # Reverse to show newest first
    results.reverse()
    
    return {"results": results, "count": len(results)}

# ============================================
# ENDPOINT 4: Drug Interactions
# ============================================
@app.get("/api/v1/drugs/{gene}")
async def get_drugs(gene: str):
    """Get known drug interactions for a gene"""
    drugs = DRUG_DATABASE.get(gene.upper(), [])
    return {
        "gene": gene,
        "drugs": drugs,
        "count": len(drugs)
    }

# ============================================
# ENDPOINT 5: Audit Log (proof of compliance)
# ============================================
@app.get("/api/v1/audit-log")
async def get_audit_log(limit: int = 50):
    """Show audit trail (compliance evidence)"""
    db = get_db()
    
    # Get last 'limit' audit logs
    logs = []
    for log in db["audit_logs"][-limit:]:
        logs.append({
            "action": log["action"],
            "resource": log["resource"],
            "user": log["user_id"],
            "timestamp": log["timestamp"]
        })
    
    # Reverse to show newest first
    logs.reverse()
    
    return {"audit_logs": logs, "count": len(logs)}

# ============================================
# ENDPOINT 7: Treatment Plan Submission
# ============================================
@app.post("/api/v1/treatment-plan")
async def create_treatment_plan(payload: dict):
    """
    Submit treatment plan with selected drugs and variants.
    NOW ENHANCED: Auto-classifies variants and suggests drugs if not provided!
    
    Accepts two formats:
    1. Simple: Just variants with gene+mutation, auto-classifies and suggests drugs
    2. Manual: Full variant objects with drugs already selected
    
    Creates audit trail for compliance.
    """
    db = get_db()
    
    try:
        variants = payload.get("variants", [])
        selected_drugs = payload.get("selected_drugs", [])
        created_by = payload.get("created_by", "unknown")
        
        # If no drugs provided, auto-classify variants and suggest drugs
        if not selected_drugs:
            selected_drugs = []
            classified_variants = []
            drug_recommendations = {}  # Track drugs by gene
            
            for variant in variants:
                gene = variant.get("gene", "UNKNOWN")
                mutation = variant.get("mutation", "unknown")
                
                # Auto-classify variant
                if "frameshift" in str(mutation).lower() or "nonsense" in str(mutation).lower():
                    classification = "PATHOGENIC"
                    acmg_score = 0.95
                elif "missense" in str(mutation).lower():
                    classification = "VUS"
                    acmg_score = 0.60
                else:
                    classification = "BENIGN"
                    acmg_score = 0.15
                
                # Add classification to variant
                classified_variant = {
                    "gene": gene,
                    "mutation": mutation,
                    "classification": classification,
                    "acmg_score": acmg_score
                }
                classified_variants.append(classified_variant)
                
                # Look up drug interactions for pathogenic/VUS variants
                if classification in ["PATHOGENIC", "VUS"]:
                    drugs = DRUG_DATABASE.get(gene.upper(), [])
                    # Initialize gene entry in recommendations
                    if gene not in drug_recommendations:
                        drug_recommendations[gene] = []
                    
                    for drug in drugs:
                        # Avoid duplicates
                        if drug not in selected_drugs:
                            selected_drugs.append(drug)
                        # Add to gene-specific recommendations
                        if drug not in drug_recommendations[gene]:
                            drug_recommendations[gene].append(drug)
            
            # Update variants with classification
            variants = classified_variants
        else:
            # Build drug recommendations from provided variants/drugs
            drug_recommendations = {}
            for variant in variants:
                gene = variant.get("gene", "UNKNOWN")
                if gene not in drug_recommendations:
                    drug_recommendations[gene] = []
                
                # Find drugs for this gene
                for drug in selected_drugs:
                    # Match drug to gene based on DRUG_DATABASE
                    for db_gene, db_drugs in DRUG_DATABASE.items():
                        if drug in db_drugs and db_gene == gene.upper():
                            if drug not in drug_recommendations[gene]:
                                drug_recommendations[gene].append(drug)
        
        # Create treatment plan record
        plan = {
            "id": str(__import__('uuid').uuid4()),
            "variants": variants,
            "selected_drugs": selected_drugs,
            "drug_recommendations": drug_recommendations,  # New field!
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        # Store in database
        if "treatment_plans" not in db:
            db["treatment_plans"] = []
        db["treatment_plans"].append(plan)
        
        # Create audit log entry (HIPAA compliance)
        db["audit_logs"].append({
            "action": "TREATMENT_PLAN_CREATED",
            "resource": f"plan:{plan['id']}",
            "user_id": created_by,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "variant_count": len(variants),
                "drug_count": len(selected_drugs),
                "drugs": [d.get("name") for d in selected_drugs],
                "auto_classified": len([v for v in variants if "classification" in v]) > 0
            }
        })
        
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "plan_id": plan["id"],
                "message": f"Treatment plan created with {len(selected_drugs)} drug(s) for {len(variants)} variant(s)",
                "variants_count": len(variants),
                "drugs_count": len(selected_drugs),
                "drug_recommendations": drug_recommendations,  # Organized by gene!
                "plan": plan
            }
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": str(e)
            }
        )

# ============================================
# ENDPOINT 8: Get Treatment Plans
# ============================================
@app.get("/api/v1/treatment-plans")
async def get_treatment_plans(limit: int = 10):
    """Retrieve recent treatment plans with drug recommendations organized by gene"""
    db = get_db()
    
    if "treatment_plans" not in db:
        return {
            "status": "success",
            "treatment_plans": [],
            "count": 0,
            "summary": {
                "total_plans": 0,
                "total_variants": 0,
                "total_drugs": 0
            }
        }
    
    plans = db["treatment_plans"][-limit:]
    plans.reverse()
    
    # Calculate summary statistics
    total_variants = sum(len(plan.get("variants", [])) for plan in plans)
    total_drugs = sum(len(plan.get("selected_drugs", [])) for plan in plans)
    
    return {
        "status": "success",
        "treatment_plans": plans,
        "count": len(plans),
        "summary": {
            "total_plans": len(plans),
            "total_variants": total_variants,
            "total_drugs": total_drugs
        }
    }

# ============================================
# ENDPOINT 6: Serve Dashboard
# ============================================
@app.get("/")
async def serve_dashboard():
    """Serve the dashboard HTML"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path, media_type="text/html")
    return {"message": "Dashboard not found"}

# ============================================
# SIMPLIFIED DRUG DATABASE
# ============================================
DRUG_DATABASE = {
    "TP53": [
        {"name": "Nutlin-3", "interaction": "MDM2 inhibitor", "grade": "III"},
        {"name": "PRIMA-1", "interaction": "p53 restoration", "grade": "II"}
    ],
    "BRCA1": [
        {"name": "Olaparib", "interaction": "PARP inhibitor", "grade": "I"},
        {"name": "Rucaparib", "interaction": "PARP inhibitor", "grade": "I"}
    ],
    "EGFR": [
        {"name": "Gefitinib", "interaction": "TKI", "grade": "I"},
        {"name": "Erlotinib", "interaction": "TKI", "grade": "I"}
    ],
    "CYP2D6": [
        {"name": "Codeine", "interaction": "Poor metabolizer", "grade": "II"},
        {"name": "Tamoxifen", "interaction": "Reduced efficacy", "grade": "II"}
    ]
}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
