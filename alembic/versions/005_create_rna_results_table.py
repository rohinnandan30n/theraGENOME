"""Create RNA-seq results table

Revision ID: 005
Revises: 004
Create Date: 2026-03-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create rna_results table for RNA-seq differential expression results."""
    op.create_table(
        'rna_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.patient_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('gene_id', sa.String(50), nullable=False),
        sa.Column('gene_name', sa.String(255), nullable=False),  # Human-readable gene symbol
        sa.Column('log2_fold_change', sa.Float, nullable=False),
        sa.Column('p_value', sa.Float, nullable=False),
        sa.Column('padj', sa.Float, nullable=False, index=True),  # Adjusted p-value
        sa.Column('base_mean', sa.Float, nullable=True),  # Average normalized count
        sa.Column('case_mean', sa.Float, nullable=True),  # Case group expression mean
        sa.Column('control_mean', sa.Float, nullable=True),  # Control group expression mean
        sa.Column('significance_flag', sa.String(20), nullable=True),  # 'up', 'down', 'stable'
        sa.Column('effect_size', sa.Float, nullable=True),  # Absolute log2FC
        sa.Column('expression_level', sa.String(20), nullable=True),  # 'high', 'medium', 'low', 'absent'
        sa.Column('transcript_biotype', sa.String(50), nullable=True),  # protein_coding, lncRNA, etc.
        sa.Column('go_annotations', JSONB, nullable=True),  # Gene Ontology terms
        sa.Column('pathway_associations', JSONB, nullable=True),  # KEGG/Reactome pathways
        sa.Column('clinical_relevance', sa.Text, nullable=True),  # Curated clinical notes
        sa.Column('metadata', JSONB, nullable=True),  # Additional processing details
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for common queries
    op.create_index('idx_rna_results_patient_id', 'rna_results', ['patient_id'])
    op.create_index('idx_rna_results_gene_id', 'rna_results', ['gene_id'])
    op.create_index('idx_rna_results_gene_name', 'rna_results', ['gene_name'])
    op.create_index('idx_rna_results_padj', 'rna_results', ['padj'])
    op.create_index('idx_rna_results_log2fc', 'rna_results', ['log2_fold_change'])
    op.create_index('idx_rna_results_significance', 'rna_results', ['significance_flag'])
    op.create_index('idx_rna_results_created_at', 'rna_results', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_rna_results_deleted_at', 'rna_results', ['deleted_at'])


def downgrade() -> None:
    """Drop rna_results table."""
    op.drop_index('idx_rna_results_deleted_at', table_name='rna_results')
    op.drop_index('idx_rna_results_created_at', table_name='rna_results')
    op.drop_index('idx_rna_results_significance', table_name='rna_results')
    op.drop_index('idx_rna_results_log2fc', table_name='rna_results')
    op.drop_index('idx_rna_results_padj', table_name='rna_results')
    op.drop_index('idx_rna_results_gene_name', table_name='rna_results')
    op.drop_index('idx_rna_results_gene_id', table_name='rna_results')
    op.drop_index('idx_rna_results_patient_id', table_name='rna_results')
    op.drop_table('rna_results')
