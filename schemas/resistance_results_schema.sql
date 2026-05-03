-- ========================================================================
-- Pathogen Resistance Results Schema (Dev 2)
-- ========================================================================
-- Purpose: Store antimicrobial resistance prediction results
-- Used by: Pathogen Resistance service, Therapy Decision Report aggregator
-- HIPAA: Compliant - no PII, encrypted storage
-- ========================================================================

CREATE TABLE IF NOT EXISTS resistance_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign key to patients table
    patient_id UUID NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    
    -- Sample and pathogen information
    sample_id VARCHAR(50) NOT NULL,
    pathogen_id VARCHAR(50) NOT NULL,
    pathogen_name VARCHAR(255),
    
    -- Resistance genes identified
    resistance_genes JSONB NOT NULL,  -- Array of {gene_id, gene_name, amr_phenotype, mechanism, coverage, depth}
    
    -- Prediction results
    predicted_phenotype VARCHAR(100),  -- e.g., "Beta-lactam resistant"
    prediction_confidence FLOAT NOT NULL CHECK (prediction_confidence >= 0 AND prediction_confidence <= 1),
    
    -- Recommendation
    antimicrobial_recommendation VARCHAR(255),
    alternative_antimicrobials TEXT,  -- JSON array of alternatives
    
    -- Model information
    model_version VARCHAR(20) DEFAULT 'v1',
    model_name VARCHAR(100) DEFAULT 'theraGENOME-Resistance-v1',
    
    -- Analysis metadata
    analysis_date TIMESTAMPTZ,
    coverage_threshold FLOAT DEFAULT 0.8,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    
    -- Audit trail
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_resistance_results_patient_id ON resistance_results(patient_id);
CREATE INDEX idx_resistance_results_sample_id ON resistance_results(sample_id);
CREATE INDEX idx_resistance_results_pathogen_id ON resistance_results(pathogen_id);
CREATE INDEX idx_resistance_results_created_at ON resistance_results(created_at DESC);
CREATE INDEX idx_resistance_results_deleted_at ON resistance_results(deleted_at) 
    WHERE deleted_at IS NULL;

-- Soft delete function
CREATE OR REPLACE FUNCTION soft_delete_resistance_result(result_id UUID)
RETURNS void AS $$
BEGIN
    UPDATE resistance_results 
    SET deleted_at = now() 
    WHERE resistance_results.result_id = soft_delete_resistance_result.result_id 
    AND deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Audit trigger
CREATE OR REPLACE FUNCTION before_update_resistance_results()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER resistance_results_before_update
BEFORE UPDATE ON resistance_results
FOR EACH ROW
EXECUTE FUNCTION before_update_resistance_results();

-- Comment for documentation
COMMENT ON TABLE resistance_results IS 
    'Stores pathogen resistance prediction results from Dev 2 Pathogen Resistance API. 
     Used by Therapy Decision Report aggregator to provide resistance summary.';

COMMENT ON COLUMN resistance_results.resistance_genes IS 
    'JSON array containing identified resistance genes with coverage, depth, and AMR phenotypes.';

COMMENT ON COLUMN resistance_results.predicted_phenotype IS 
    'Predicted antimicrobial resistance phenotype (e.g., "Beta-lactam resistant", "Fluoroquinolone resistant").';
