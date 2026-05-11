-- Variant schema for genomic data storage
CREATE TABLE IF NOT EXISTS variants (
    id SERIAL PRIMARY KEY,
    job_id UUID NOT NULL,
    chrom VARCHAR(20) NOT NULL,
    pos INTEGER NOT NULL,
    ref VARCHAR(1000) NOT NULL,
    alt VARCHAR(1000) NOT NULL,
    qual FLOAT,
    info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_job_id (job_id),
    INDEX idx_chrom_pos (chrom, pos)
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    variant_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model performance tracking table
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    variant_id VARCHAR(255),
    model_version VARCHAR(50) NOT NULL,
    predicted_label VARCHAR(50) NOT NULL,
    true_label VARCHAR(50),
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at),
    INDEX idx_model_version (model_version),
    INDEX idx_variant_id (variant_id)
);
