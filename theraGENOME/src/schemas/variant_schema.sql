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
