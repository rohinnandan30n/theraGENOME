-- Variant Results Table
-- Stores classification results for patient variants with complete history and audit trail

CREATE TABLE IF NOT EXISTS variant_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    variant_id VARCHAR(255) NOT NULL,
    chrom VARCHAR(2) NOT NULL,
    pos INTEGER NOT NULL,
    ref VARCHAR(1000) NOT NULL,
    alt VARCHAR(1000) NOT NULL,
    prediction VARCHAR(50) NOT NULL CHECK (prediction IN ('Pathogenic', 'Benign', 'VUS')),
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    probabilities JSONB NOT NULL DEFAULT '{}',
    model_version VARCHAR(10) NOT NULL DEFAULT 'v2',
    feature_importance JSONB,
    clinical_notes TEXT,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);

-- Indexes for common queries
CREATE INDEX idx_variant_results_patient_id ON variant_results(patient_id) WHERE NOT is_deleted;
CREATE INDEX idx_variant_results_variant_id ON variant_results(variant_id) WHERE NOT is_deleted;
CREATE INDEX idx_variant_results_created_at ON variant_results(created_at) WHERE NOT is_deleted;
CREATE INDEX idx_variant_results_prediction ON variant_results(prediction) WHERE NOT is_deleted;
CREATE INDEX idx_variant_results_patient_id_created_at ON variant_results(patient_id, created_at DESC) WHERE NOT is_deleted;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON variant_results TO app_user;
