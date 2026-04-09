"""
TheraGenome Database Layer
===========================
Handles database initialization and connections.
Supports SQLite for development, PostgreSQL for production.
"""

import os
import sqlite3
import json
from pathlib import Path
from typing import Any, Optional

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # sqlite or postgres
DB_PATH = os.getenv("DB_SQLITE_PATH", "theragenome.db")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "genomic_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")


def init_sqlite_db():
    """Initialize SQLite database with sample scheme and data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create variants table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variants (
            id INTEGER PRIMARY KEY,
            gene TEXT NOT NULL,
            variant TEXT NOT NULL,
            effect TEXT,
            pathogenicity TEXT,
            clinical_significance TEXT,
            population_frequency REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create resistance markers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resistance_markers (
            id INTEGER PRIMARY KEY,
            gene TEXT NOT NULL,
            mechanism TEXT,
            antibiotic_class TEXT,
            confidence REAL,
            organism TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create drug safety table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug_safety (
            id INTEGER PRIMARY KEY,
            drug_name TEXT NOT NULL,
            organ_system TEXT,
            toxicity_level TEXT,
            description TEXT,
            reversible BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Load sample pharmacogene variants (key genes for drug metabolism)
    sample_variants = [
        ("CYP2D6", "CYP2D6*1", "normal_function", "benign", "CYP2D6 normal function allele - normal metabolizer"),
        ("CYP2D6", "CYP2D6*4", "loss_of_function", "pathogenic", "CYP2D6*4 - poor metabolizer allele"),
        ("CYP2D6", "CYP2D6*41", "reduced_function", "likely_pathogenic", "CYP2D6*41 - intermediate metabolizer"),
        ("CYP2C19", "CYP2C19*1", "normal_function", "benign", "CYP2C19 normal function - extensive metabolizer"),
        ("CYP2C19", "CYP2C19*2", "loss_of_function", "pathogenic", "CYP2C19*2 - poor metabolizer allele"),
        ("CYP2C19", "CYP2C19*3", "loss_of_function", "pathogenic", "CYP2C19*3 - poor metabolizer"),
        ("CYP2C9", "CYP2C9*1", "normal_function", "benign", "CYP2C9 normal function"),
        ("CYP2C9", "CYP2C9*2", "reduced_function", "likely_pathogenic", "CYP2C9*2 - reduced warfarin metabolism"),
        ("CYP2C9", "CYP2C9*3", "reduced_function", "likely_pathogenic", "CYP2C9*3 - significantly reduced metabolism"),
        ("TPMT", "TPMT*1", "normal_function", "benign", "TPMT normal function"),
        ("TPMT", "TPMT*2", "loss_of_function", "pathogenic", "TPMT*2 - low activity, risk for thiopurine toxicity"),
        ("TPMT", "TPMT*3A", "loss_of_function", "pathogenic", "TPMT*3A - deficient activity"),
        ("HLA-B", "HLA-B*5701", "loss_of_function", "pathogenic", "HLA-B*5701 - contraindication for abacavir"),
        ("DPYD", "DPYD*2A", "loss_of_function", "pathogenic", "DPYD*2A - deficient, 5-FU/capecitabine contraindicated"),
        ("NAT2", "NAT2*4", "normal_function", "benign", "NAT2*4 - fast acetylator"),
        ("NAT2", "NAT2*5", "reduced_function", "likely_pathogenic", "NAT2*5 - slow acetylator phenotype"),
        ("G6PD", "G6PD*B", "normal_function", "benign", "G6PD normal function"),
        ("G6PD", "G6PD*A-", "loss_of_function", "pathogenic", "G6PD deficiency - risk of hemolysis with oxidative stressors"),
    ]
    
    for gene, variant, effect, pathogenicity, clinical_sig in sample_variants:
        cursor.execute("""
            INSERT OR IGNORE INTO variants 
            (gene, variant, effect, pathogenicity, clinical_significance)
            VALUES (?, ?, ?, ?, ?)
        """, (gene, variant, effect, pathogenicity, clinical_sig))
    
    # Load additional variants from JSON if available
    sample_variants_path = Path(__file__).parent.parent / "demo_variants.json"
    if sample_variants_path.exists():
        with open(sample_variants_path, 'r') as f:
            variants = json.load(f)
            for variant in variants:
                cursor.execute("""
                    INSERT OR IGNORE INTO variants 
                    (gene, variant, effect, pathogenicity, clinical_significance)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    variant.get("gene"),
                    variant.get("mutation"),
                    variant.get("type"),
                    "unknown",
                    variant.get("gene", "") + " variant"
                ))
    
    # Load sample resistance markers
    sample_resistance = [
        ("mecA", "beta_lactam_resistance", "beta_lactam", 0.95, "MRSA"),
        ("darA", "fluoroquinolone_resistance", "fluoroquinolone", 0.88, "S. aureus"),
        ("vanA", "vancomycin_resistance", "glycopeptide", 0.92, "Enterococcus"),
        ("blaCTX-M", "extended_spectrum_beta_lactamase", "beta_lactam", 0.90, "Gram-negative"),
        ("aac(2')-I", "aminoglycoside_resistance", "aminoglycoside", 0.85, "Acinetobacter"),
    ]
    
    for gene, mechanism, antibiotic_class, confidence, organism in sample_resistance:
        cursor.execute("""
            INSERT OR IGNORE INTO resistance_markers 
            (gene, mechanism, antibiotic_class, confidence, organism)
            VALUES (?, ?, ?, ?, ?)
        """, (gene, mechanism, antibiotic_class, confidence, organism))
    
    # Load sample drug safety data
    sample_drugs = [
        # Amoxicillin (Antibiotic)
        ("amoxicillin", "hepatic", "mild", "Elevated liver enzymes with prolonged use", True),
        ("amoxicillin", "renal", "mild", "Creatinine elevation in CKD patients", True),
        ("amoxicillin", "cardiac", "low", "Minimal cardiac effects. Generally safe for cardiac patients.", True),
        ("amoxicillin", "respiratory", "low", "No respiratory effects", True),
        
        # Warfarin (Anticoagulant)
        ("warfarin", "cardiac", "high", "Therapeutic anticoagulant for cardiac conditions. Requires INR monitoring.", True),
        ("warfarin", "gastrointestinal", "high", "GI bleeding risk. Monitor for signs of bleeding.", False),
        ("warfarin", "renal", "mild", "Clearance affected by renal function. Adjust dosing as needed.", True),
        ("warfarin", "hepatic", "high", "Metabolism dependent on hepatic function. Critical dosing adjustments needed.", True),
        
        # Metformin (Antidiabetic)
        ("metformin", "renal", "high", "Lactic acidosis risk in renal impairment. Contraindicated if eGFR <30.", True),
        ("metformin", "cardiac", "low", "No direct cardiac effects. Cardiovascular benefits in diabetes.", True),
        ("metformin", "hepatic", "low", "Not metabolized hepatically. Safe in liver disease.", True),
        ("metformin", "gastrointestinal", "mild", "GI upset common initially. Use extended-release formulation.", True),
        
        # Ciprofloxacin (Fluoroquinolone)
        ("ciprofloxacin", "cardiac", "low", "Low cardiac risk. Safe for most cardiac patients.", True),
        ("ciprofloxacin", "renal", "mild", "Renal excretion significant. Reduce dose in severe renal impairment.", True),
        ("ciprofloxacin", "hepatic", "low", "Minimal hepatic metabolism. Safe in liver disease.", True),
        ("ciprofloxacin", "gastrointestinal", "mild", "GI tolerability varies. Take with water, avoid dairy products.", True),
        
        # Lisinopril (ACE Inhibitor)
        ("lisinopril", "cardiac", "low", "Beneficial for heart failure and hypertension management.", True),
        ("lisinopril", "renal", "mild", "May cause initial creatinine elevation. Monitor K+ and renal function.", True),
        ("lisinopril", "hepatic", "low", "No hepatic metabolism. Safe in liver disease.", True),
        ("lisinopril", "gastrointestinal", "low", "Generally well-tolerated. Cough is common side effect.", True),
        
        # Aspirin (NSAID)
        ("aspirin", "cardiac", "low", "Cardioprotective at low doses. Prevents thrombotic events.", True),
        ("aspirin", "gastrointestinal", "high", "GI bleeding and ulcer risk, especially long-term use.", False),
        ("aspirin", "renal", "mild", "May affect renal function. Use cautiously in CKD.", True),
        ("aspirin", "hepatic", "mild", "Hepatotoxicity possible at high doses. Monitor LFTs.", True),
        
        # Vancomycin (Glycopeptide)
        ("vancomycin", "cardiac", "low", "Suitable for cardiac patients. Monitor vital signs during infusion.", True),
        ("vancomycin", "renal", "high", "Nephrotoxicity risk. Monitor trough levels and serum creatinine.", True),
        ("vancomycin", "hepatic", "low", "No hepatic metabolism. Safe in liver disease.", True),
        ("vancomycin", "gastrointestinal", "low", "IV formulation. Minimal GI effects.", True),
        
        # Linezolid (Oxazolidinone)
        ("linezolid", "cardiac", "low", "Generally safe. Monitor QT interval if prolongation risk.", True),
        ("linezolid", "renal", "low", "Not renally cleared significantly. Safe in renal impairment.", True),
        ("linezolid", "hepatic", "mild", "Hepatic metabolism occurs. Use caution in severe liver disease.", True),
        ("linezolid", "gastrointestinal", "mild", "GI upset possible. Take with or without food.", True),
        
        # Ibuprofen (NSAID)
        ("ibuprofen", "renal", "moderate", "Acute kidney injury with chronic use", True),
        ("ibuprofen", "cardiac", "mild", "Minor effects. Safe in most cardiac conditions.", True),
        ("ibuprofen", "gastrointestinal", "moderate", "Increased GI bleeding risk with chronic use.", False),
    ]
    
    for drug_name, organ_system, toxicity_level, description, reversible in sample_drugs:
        cursor.execute("""
            INSERT OR IGNORE INTO drug_safety 
            (drug_name, organ_system, toxicity_level, description, reversible)
            VALUES (?, ?, ?, ?, ?)
        """, (drug_name, organ_system, toxicity_level, description, reversible))
    
    conn.commit()
    conn.close()
    print(f"✅ SQLite database initialized at {DB_PATH}")


def get_db_connection():
    """Get database connection (SQLite or PostgreSQL)"""
    if DB_TYPE == "sqlite":
        # Ensure database exists
        if not Path(DB_PATH).exists():
            init_sqlite_db()
        return sqlite3.connect(DB_PATH)
    else:
        # PostgreSQL connection (requires psycopg2)
        try:
            import psycopg2
            return psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
        except ImportError:
            print("❌ psycopg2 not installed. Falling back to SQLite.")
            return get_db_connection()  # fallback to sqlite


def query_variants(gene: Optional[str] = None) -> list[dict[str, Any]]:
    """Query variants from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if gene:
        cursor.execute("SELECT * FROM variants WHERE gene LIKE ?", (f"%{gene}%",))
    else:
        cursor.execute("SELECT * FROM variants")
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(zip(columns, row)) for row in rows]


def query_resistance_markers(organism: Optional[str] = None) -> list[dict[str, Any]]:
    """Query resistance markers from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if organism:
        cursor.execute("SELECT * FROM resistance_markers WHERE organism LIKE ?", (f"%{organism}%",))
    else:
        cursor.execute("SELECT * FROM resistance_markers")
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(zip(columns, row)) for row in rows]


def query_drug_safety(drug_name: Optional[str] = None) -> list[dict[str, Any]]:
    """Query drug safety data from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if drug_name:
        cursor.execute("SELECT * FROM drug_safety WHERE drug_name LIKE ?", (f"%{drug_name}%",))
    else:
        cursor.execute("SELECT * FROM drug_safety")
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(zip(columns, row)) for row in rows]


# Initialize database on module load
if not Path(DB_PATH).exists() and DB_TYPE == "sqlite":
    init_sqlite_db()
