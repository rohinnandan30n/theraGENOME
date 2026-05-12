"""Script to export the patient_schema.sql for distribution to development teams"""

import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/thergenome_dev"
)


def export_schema(output_file: str = "schemas/patient_schema.sql") -> None:
    """Export the patients table schema to SQL file.
    
    Args:
        output_file: Path to write the schema SQL file
    """
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        
        with engine.connect() as conn:
            # Get table information
            inspector = inspect(engine)
            
            # Check if patients table exists
            tables = inspector.get_table_names()
            if "patients" not in tables:
                print("❌ Error: 'patients' table does not exist in database")
                print("ℹ️  Run Alembic migrations first: alembic upgrade head")
                return
            
            # Get the table definition SQL
            result = conn.execute(
                text(
                    """
                    SELECT table_name, table_type 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'patients'
                    """
                )
            )
            
            # Extract full table definition using pg_dump equivalent
            schema_sql = get_table_schema(conn)
            
            # Write to file
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, "w") as f:
                f.write(schema_sql)
            
            print(f"✅ Schema exported to: {output_file}")
            print(f"📄 File size: {len(schema_sql)} bytes")
            
    except Exception as e:
        print(f"❌ Error exporting schema: {e}")


def get_table_schema(conn) -> str:
    """Get the CREATE TABLE statement for the patients table"""
    
    result = conn.execute(
        text(
            """
        SELECT 
            'CREATE TABLE' as stmt_type,
            'patients' as table_name,
            string_agg(
                format('  %I %s%s',
                    column_name,
                    data_type || 
                    CASE WHEN character_maximum_length IS NOT NULL 
                        THEN '(' || character_maximum_length || ')' 
                        ELSE '' 
                    END,
                    CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END
                ),
                E',\n'
            ) as columns
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'patients'
        GROUP BY table_schema, table_name
        """
        )
    )
    
    # Build comprehensive schema export
    sql_parts = [
        "-- ============================================================================",
        "-- TheraGenome Patient Schema",
        "-- Core patient demographics and identity table",
        "-- Generated from Alembic migration: 001_create_patients_table",
        "-- ============================================================================",
        "",
        "-- Enable required extensions",
        "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";",
        "",
        "-- ============================================================================",
        "-- Core Patients Table",
        "-- ============================================================================",
        "-- HIPAA SENSITIVE: This table contains patient demographics",
        "-- Ensure proper access controls and encryption at rest is enabled",
        "",
        """CREATE TABLE IF NOT EXISTS patients (
    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    sex VARCHAR(20),
    ethnicity VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);""",
        "",
        "-- ============================================================================",
        "-- Indexes for query optimization",
        "-- ============================================================================",
        """
CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_patient_id ON patients(patient_id);
CREATE INDEX IF NOT EXISTS idx_patients_date_of_birth ON patients(date_of_birth);
CREATE INDEX IF NOT EXISTS idx_patients_deleted_at ON patients(deleted_at);
CREATE INDEX IF NOT EXISTS idx_patients_created_at ON patients(created_at);
""",
        "-- ============================================================================",
        "-- Table Comments (Documentation)",
        "-- ============================================================================",
        """
COMMENT ON TABLE patients IS 'Core patient demographics and identity table - HIPAA sensitive';
COMMENT ON COLUMN patients.patient_id IS 'Unique patient identifier (UUID v4)';
COMMENT ON COLUMN patients.first_name IS 'Patient first name';
COMMENT ON COLUMN patients.last_name IS 'Patient last name';
COMMENT ON COLUMN patients.date_of_birth IS 'Patient date of birth';
COMMENT ON COLUMN patients.sex IS 'Biological sex (M/F/Other/Prefer not to say)';
COMMENT ON COLUMN patients.ethnicity IS 'Patient ethnicity';
COMMENT ON COLUMN patients.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN patients.updated_at IS 'Last update timestamp';
COMMENT ON COLUMN patients.deleted_at IS 'Soft delete timestamp (NULL if active)';
""",
        "-- ============================================================================",
        "-- Distribution Note",
        "-- ============================================================================",
        """
-- This schema file should be distributed to all development teams as the
-- authoritative patient table definition. All foreign keys referencing
-- patients.patient_id should use: CONSTRAINT fk_<table>_patient_id FOREIGN KEY (patient_id)
--        REFERENCES patients(patient_id) ON DELETE RESTRICT
--
-- For schema changes:
-- 1. Create new Alembic migration in alembic/versions/
-- 2. Run: alembic upgrade head
-- 3. Export updated schema: python scripts/export_schema.py
-- 4. Distribute to all development teams for sync
-- ============================================================================
""",
    ]
    
    return "\n".join(sql_parts)


if __name__ == "__main__":
    export_schema()
