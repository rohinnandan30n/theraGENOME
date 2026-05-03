"""
Seed script for generating synthetic HIPAA-safe patient records.

This script uses Faker to create realistic synthetic patient data with:
- Valid demographic distributions
- Only synthetic/fake data (no real PII)
- Realistic age distributions
- Diverse ethnicities and sex distributions
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid

from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/thergenome_dev"
)
BATCH_SIZE = 100
NUM_PATIENTS = 100

# Sex options
SEX_OPTIONS = ["M", "F", "Other", "Prefer not to say"]

# Ethnicity distribution
ETHNICITY_OPTIONS = [
    "Caucasian",
    "African American",
    "Hispanic/Latino",
    "Asian",
    "Native American",
    "Pacific Islander",
    "Middle Eastern",
    "Multi-racial",
    "Other",
]


def generate_synthetic_patient() -> Dict[str, Any]:
    """Generate a synthetic patient record with realistic demographics.
    
    Returns:
        Dictionary with patient data aligned to patients table schema
    """
    fake = Faker()
    
    # Generate realistic age distribution (18-95 years old)
    # Skew toward older ages for medical population
    import random
    age = max(
        18,
        int(
            random.gauss(50, 20)
        ),  # Normal distribution centered at 50, std 20
    )
    age = min(age, 95)  # Cap at 95
    
    date_of_birth = datetime.now().date() - timedelta(
        days=age * 365 + random.randint(0, 365)
    )
    
    return {
        "patient_id": str(uuid.uuid4()),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "date_of_birth": date_of_birth,
        "sex": random.choice(SEX_OPTIONS),
        "ethnicity": random.choice(ETHNICITY_OPTIONS),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "deleted_at": None,
    }


def seed_patients(num_patients: int = NUM_PATIENTS) -> None:
    """
    Seed the database with synthetic patient records.
    
    Args:
        num_patients: Number of synthetic patients to create (default 100)
    """
    print(f"🌱 Connecting to database: {DATABASE_URL}")
    
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("ℹ️  Make sure PostgreSQL is running and credentials are correct.")
        print(f"ℹ️  Update DATABASE_URL in .env file")
        return
    
    try:
        # Generate synthetic patients in batches
        print(f"\n🧬 Generating {num_patients} synthetic patient records...")
        
        patients = [generate_synthetic_patient() for _ in range(num_patients)]
        
        # Insert using raw SQL for better control and debugging
        with engine.begin() as conn:
            # Check if table exists
            result = conn.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'patients'
                    )
                    """
                )
            )
            table_exists = result.scalar()
            
            if not table_exists:
                print("❌ Error: 'patients' table does not exist!")
                print("ℹ️  Run Alembic migrations first: alembic upgrade head")
                return
            
            # Batch insert
            for i in range(0, len(patients), BATCH_SIZE):
                batch = patients[i : i + BATCH_SIZE]
                
                # Prepare the INSERT statement
                insert_stmt = text(
                    """
                    INSERT INTO patients 
                    (patient_id, first_name, last_name, date_of_birth, sex, ethnicity, 
                     created_at, updated_at, deleted_at)
                    VALUES (:patient_id, :first_name, :last_name, :date_of_birth, :sex, 
                            :ethnicity, :created_at, :updated_at, :deleted_at)
                    """
                )
                
                for patient in batch:
                    conn.execute(insert_stmt, patient)
                
                inserted = min(i + BATCH_SIZE, len(patients))
                print(f"  ✓ Inserted {inserted}/{num_patients} records")
        
        print(f"\n✅ Successfully seeded {num_patients} synthetic patient records!")
        
        # Show summary statistics
        with engine.begin() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT 
                        COUNT(*) as total_patients,
                        MIN(date_of_birth) as oldest_patient,
                        MAX(date_of_birth) as youngest_patient
                    FROM patients
                    WHERE deleted_at IS NULL
                    """
                )
            )
            row = result.fetchone()
            print(f"\n📊 Summary Statistics:")
            print(f"  Total Active Patients: {row[0]}")
            print(f"  Oldest Patient DOB: {row[1]}")
            print(f"  Youngest Patient DOB: {row[2]}")
            
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    num_patients = NUM_PATIENTS
    
    # Allow custom number via command line
    if len(sys.argv) > 1:
        try:
            num_patients = int(sys.argv[1])
            print(f"Using custom patient count: {num_patients}")
        except ValueError:
            print(f"Invalid patient count: {sys.argv[1]}")
            sys.exit(1)
    
    seed_patients(num_patients)
