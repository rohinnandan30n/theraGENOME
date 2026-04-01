"""Create proteomics results table

Revision ID: 006
Revises: 005
Create Date: 2026-03-31 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create protein_results table for proteomics data."""
    op.create_table(
        'protein_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.patient_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('protein_id', sa.String(100), nullable=False),
        sa.Column('protein_name', sa.String(255), nullable=False),
        sa.Column('gene_name', sa.String(100), nullable=True),  # Associated gene
        sa.Column('uniprot_id', sa.String(10), nullable=True),  # UniProt accession
        sa.Column('lfq_intensity', sa.Float, nullable=False),  # Label-free quantification
        sa.Column('log2_intensity', sa.Float, nullable=False),  # Log2-normalized LFQ
        sa.Column('peptide_count', sa.Integer, nullable=True),  # Number of quantified peptides
        sa.Column('unique_peptides', sa.Integer, nullable=True),  # Unique peptide count
        sa.Column('razor_peptides', sa.Integer, nullable=True),  # Razor peptides
        sa.Column('sequence_coverage', sa.Float, nullable=True),  # Sequence coverage %
        sa.Column('molecular_weight', sa.Float, nullable=True),  # MW in kDa
        sa.Column('protein_probability', sa.Float, nullable=True),  # Identification probability
        sa.Column('intensity_ratio', sa.Float, nullable=True),  # Case/control ratio
        sa.Column('fold_change', sa.Float, nullable=True),  # Absolute or log2 fold-change
        sa.Column('protein_class', sa.String(50), nullable=True),  # Enzyme, receptor, etc.
        sa.Column('pathway_associations', JSONB, nullable=True),  # Pathways from KEGG
        sa.Column('post_modifications', JSONB, nullable=True),  # Phosphorylation, ubiquitination, etc.
        sa.Column('tissue_expression', JSONB, nullable=True),  # Tissue-specific data
        sa.Column('disease_associations', JSONB, nullable=True),  # Disease/phenotype links
        sa.Column('drug_target_info', JSONB, nullable=True),  # DrugBank interaction data
        sa.Column('clinical_significance', sa.Text, nullable=True),  # Clinical relevance notes
        sa.Column('metadata', JSONB, nullable=True),  # Additional processing details
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create comprehensive indexes
    op.create_index('idx_protein_results_patient_id', 'protein_results', ['patient_id'])
    op.create_index('idx_protein_results_protein_id', 'protein_results', ['protein_id'])
    op.create_index('idx_protein_results_protein_name', 'protein_results', ['protein_name'])
    op.create_index('idx_protein_results_uniprot_id', 'protein_results', ['uniprot_id'])
    op.create_index('idx_protein_results_gene_name', 'protein_results', ['gene_name'])
    op.create_index('idx_protein_results_log2_intensity', 'protein_results', ['log2_intensity'])
    op.create_index('idx_protein_results_fold_change', 'protein_results', ['fold_change'])
    op.create_index('idx_protein_results_protein_class', 'protein_results', ['protein_class'])
    op.create_index('idx_protein_results_created_at', 'protein_results', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_protein_results_deleted_at', 'protein_results', ['deleted_at'])


def downgrade() -> None:
    """Drop protein_results table."""
    op.drop_index('idx_protein_results_deleted_at', table_name='protein_results')
    op.drop_index('idx_protein_results_created_at', table_name='protein_results')
    op.drop_index('idx_protein_results_protein_class', table_name='protein_results')
    op.drop_index('idx_protein_results_fold_change', table_name='protein_results')
    op.drop_index('idx_protein_results_log2_intensity', table_name='protein_results')
    op.drop_index('idx_protein_results_gene_name', table_name='protein_results')
    op.drop_index('idx_protein_results_uniprot_id', table_name='protein_results')
    op.drop_index('idx_protein_results_protein_name', table_name='protein_results')
    op.drop_index('idx_protein_results_protein_id', table_name='protein_results')
    op.drop_index('idx_protein_results_patient_id', table_name='protein_results')
    op.drop_table('protein_results')
