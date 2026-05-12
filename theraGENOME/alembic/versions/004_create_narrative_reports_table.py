"""Create narrative_reports table

Revision ID: 004_create_narrative_reports_table
Revises: 003_create_fl_rounds_table
Create Date: 2026-03-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '004_create_narrative_reports_table'
down_revision = '003_create_fl_rounds_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create narrative_reports table for Task 4.5.
    
    Stores generated clinical narratives from LLM with SHAP explanations.
    """
    op.create_table(
        'narrative_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('therapy_report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Narrative content
        sa.Column('narrative_text', sa.Text(), nullable=False),
        sa.Column('narrative_sections', postgresql.JSON(), nullable=True),
        
        # SHAP explanations
        sa.Column('variant_shap_json', postgresql.JSON(), nullable=True),
        sa.Column('resistance_shap_json', postgresql.JSON(), nullable=True),
        sa.Column('toxicity_shap_json', postgresql.JSON(), nullable=True),
        
        # Generation metadata
        sa.Column('llm_model_used', sa.String(255), nullable=False),
        sa.Column('generation_duration_seconds', sa.Float(), nullable=True),
        sa.Column('generation_temperature', sa.Float(), nullable=False),
        
        # Quality metrics
        sa.Column('readability_score', sa.Float(), nullable=True),
        sa.Column('medical_terminology_score', sa.Float(), nullable=True),
        sa.Column('completeness_score', sa.Float(), nullable=True),
        
        # Audit trail
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('clinician_id', sa.String(255), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for query optimization
    op.create_index('idx_narrative_reports_therapy_report_id', 'narrative_reports', ['therapy_report_id'])
    op.create_index('idx_narrative_reports_patient_id', 'narrative_reports', ['patient_id'])
    op.create_index('idx_narrative_reports_created_at_desc', 'narrative_reports', ['created_at'], postgresql_using='btree')
    op.create_index('idx_narrative_reports_clinician_id', 'narrative_reports', ['clinician_id'])
    op.create_index('idx_narrative_reports_deleted_at', 'narrative_reports', ['deleted_at'])


def downgrade() -> None:
    """Downgrade: drop narrative_reports table."""
    op.drop_index('idx_narrative_reports_deleted_at', table_name='narrative_reports')
    op.drop_index('idx_narrative_reports_clinician_id', table_name='narrative_reports')
    op.drop_index('idx_narrative_reports_created_at_desc', table_name='narrative_reports')
    op.drop_index('idx_narrative_reports_patient_id', table_name='narrative_reports')
    op.drop_index('idx_narrative_reports_therapy_report_id', table_name='narrative_reports')
    op.drop_table('narrative_reports')
