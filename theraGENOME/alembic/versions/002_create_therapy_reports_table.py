"""Create therapy_reports table for decision aggregation

Revision ID: 002_create_therapy_reports_table
Revises: 001_create_patients_table
Create Date: 2026-03-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_create_therapy_reports_table'
down_revision = '001_create_patients_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create therapy_reports table with all required columns."""
    
    # Create ENUM types
    op.execute("""
        CREATE TYPE report_status_enum AS ENUM (
            'complete',
            'partial',
            'error',
            'timeout'
        )
    """)
    
    # Create therapy_reports table
    op.create_table(
        'therapy_reports',
        sa.Column('report_id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sample_id', sa.String(50), nullable=False),
        
        # Variant summary (from Dev 1)
        sa.Column('variant_summary', postgresql.JSON, nullable=True),
        sa.Column('variant_classification', sa.String(50), nullable=True),
        sa.Column('variant_confidence', sa.Float, nullable=True),
        sa.Column('variant_result_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Resistance summary (from Dev 2)
        sa.Column('resistance_summary', postgresql.JSON, nullable=True),
        sa.Column('predicted_phenotype', sa.String(100), nullable=True),
        sa.Column('resistance_confidence', sa.Float, nullable=True),
        sa.Column('resistance_result_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Toxicity summary (from Dev 3)
        sa.Column('toxicity_summary', postgresql.JSON, nullable=True),
        sa.Column('toxicity_risk', sa.String(20), nullable=True),  # Low, Medium, High, Critical
        sa.Column('toxicity_confidence', sa.Float, nullable=True),
        sa.Column('drug_interactions', postgresql.JSON, nullable=True),
        
        # Therapy recommendation
        sa.Column('recommended_drug', sa.String(100), nullable=True),
        sa.Column('alternative_drugs', postgresql.JSON, nullable=True),  -- Array of alternatives
        sa.Column('recommendation_confidence', sa.Float, nullable=True),
        sa.Column('recommendation_rationale', sa.Text, nullable=True),
        
        # Drug candidates input
        sa.Column('drug_candidates', postgresql.JSON, nullable=False),  -- Array of candidate drugs
        
        # Service call results and timing
        sa.Column('status', sa.Enum('complete', 'partial', 'error', 'timeout', 
                                     name='report_status_enum'), 
                  default='complete', nullable=False),
        sa.Column('variant_service_status', sa.String(20), default='success'),  -- success, timeout, error
        sa.Column('resistance_service_status', sa.String(20), default='success'),
        sa.Column('toxicity_service_status', sa.String(20), default='success'),
        
        # Service latencies (milliseconds)
        sa.Column('variant_latency_ms', sa.Integer, nullable=True),
        sa.Column('resistance_latency_ms', sa.Integer, nullable=True),
        sa.Column('toxicity_latency_ms', sa.Integer, nullable=True),
        
        # Error information
        sa.Column('error_messages', postgresql.JSON, nullable=True),  -- {service: error_msg}
        
        # Metadata
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), 
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), 
                  server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        
        # Audit trail
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('clinician_id', sa.String(100), nullable=True),
        
        # Primary key and foreign key
        sa.PrimaryKeyConstraint('report_id'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], 
                                ondelete='CASCADE'),
        sa.Index('idx_therapy_reports_patient_id', 'patient_id'),
        sa.Index('idx_therapy_reports_sample_id', 'sample_id'),
        sa.Index('idx_therapy_reports_created_at', 'created_at', postgresql.DESC),
        sa.Index('idx_therapy_reports_status', 'status'),
        sa.Index('idx_therapy_reports_deleted_at', 'deleted_at', 
                 postgresql_where=sa.text('deleted_at IS NULL')),
    )
    
    # Create trigger function for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_therapy_reports_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger
    op.execute("""
        CREATE TRIGGER therapy_reports_before_update
        BEFORE UPDATE ON therapy_reports
        FOR EACH ROW
        EXECUTE FUNCTION update_therapy_reports_timestamp();
    """)
    
    # Grant permissions
    op.execute("""
        GRANT SELECT, INSERT, UPDATE, DELETE ON therapy_reports TO app_user;
    """)


def downgrade() -> None:
    """Drop therapy_reports table and associated objects."""
    
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS therapy_reports_before_update ON therapy_reports")
    
    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS update_therapy_reports_timestamp()")
    
    # Drop table
    op.drop_table('therapy_reports')
    
    # Drop ENUM type
    op.execute("DROP TYPE IF EXISTS report_status_enum")
