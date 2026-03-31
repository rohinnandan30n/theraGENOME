-- ============================================================================
-- TheraGenome Patient Schema
-- Core patient demographics and identity table
-- Generated from Alembic migration: 001_create_patients_table
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Core Patients Table
-- ============================================================================
-- HIPAA SENSITIVE: This table contains patient demographics
-- Ensure proper access controls and encryption at rest is enabled

CREATE TABLE IF NOT EXISTS patients (
    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    sex VARCHAR(20),
    ethnicity VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- ============================================================================
-- Indexes for query optimization
-- ============================================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_patient_id ON patients(patient_id);
CREATE INDEX IF NOT EXISTS idx_patients_date_of_birth ON patients(date_of_birth);
CREATE INDEX IF NOT EXISTS idx_patients_deleted_at ON patients(deleted_at);
CREATE INDEX IF NOT EXISTS idx_patients_created_at ON patients(created_at);

-- ============================================================================
-- Table Comments (Documentation)
-- ============================================================================

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

-- ============================================================================
-- Distribution Note
-- ============================================================================
-- This schema file should be distributed to all development teams as the
-- authoritative patient table definition. All foreign keys referencing
-- patients.patient_id should use:
--
--   CONSTRAINT fk_<table>_patient_id FOREIGN KEY (patient_id)
--        REFERENCES patients(patient_id) ON DELETE RESTRICT
--
-- For schema changes:
-- 1. Create new Alembic migration in alembic/versions/
-- 2. Run: alembic upgrade head
-- 3. Export updated schema: python scripts/export_schema.py
-- 4. Distribute to all development teams for sync
-- ============================================================================
