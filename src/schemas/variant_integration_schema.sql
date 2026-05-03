-- Variant Database Integration Schema
-- Tables for ClinVar variants and gnomAD enriched data

CREATE TABLE IF NOT EXISTS clinvar_variants (
    id SERIAL PRIMARY KEY,
    variation_id VARCHAR(50) UNIQUE NOT NULL,
    rcv_id VARCHAR(50) UNIQUE,
    gene_symbol VARCHAR(100),
    hgvs_expression VARCHAR(255) UNIQUE,
    variant_type VARCHAR(50),
    ref_allele VARCHAR(1000),
    alt_allele VARCHAR(1000),
    clinical_significance VARCHAR(255),
    review_status VARCHAR(50),
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_variation_id (variation_id),
    INDEX idx_rcv_id (rcv_id),
    INDEX idx_hgvs (hgvs_expression),
    INDEX idx_gene_symbol (gene_symbol)
);

CREATE TABLE IF NOT EXISTS gnomad_frequencies (
    id SERIAL PRIMARY KEY,
    variant_id VARCHAR(50) NOT NULL,
    clinvar_variation_id VARCHAR(50),
    chrom VARCHAR(5),
    pos INTEGER,
    ref VARCHAR(1000),
    alt VARCHAR(1000),
    exome_ac INTEGER,
    exome_an INTEGER,
    exome_af FLOAT,
    genome_ac INTEGER,
    genome_an INTEGER,
    genome_af FLOAT,
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clinvar_variation_id) REFERENCES clinvar_variants(variation_id),
    UNIQUE INDEX idx_variant_id (variant_id),
    INDEX idx_chrom_pos (chrom, pos)
);

CREATE TABLE IF NOT EXISTS enriched_variants (
    id SERIAL PRIMARY KEY,
    variant_id VARCHAR(50) UNIQUE NOT NULL,
    clinvar_data JSON,
    gnomad_data JSON,
    hgvs_mapping VARCHAR(255),
    enriched_metadata JSON,
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_variant_id (variant_id)
);
