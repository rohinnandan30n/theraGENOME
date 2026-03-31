"""Create fl_rounds table for federated learning metrics.

Revision ID: 003
Revises: 002
Create Date: 2026-03-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for round status
    status_enum = postgresql.ENUM(
        'pending',
        'in_progress',
        'completed',
        'failed',
        name='fl_round_status',
        create_type=True
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    # Create fl_rounds table
    op.create_table(
        'fl_rounds',
        sa.Column('round_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('num_clients', sa.Integer(), nullable=False),
        sa.Column('min_clients_available', sa.Integer(), nullable=True),
        sa.Column('aggregated_loss', sa.Float(), nullable=True),
        sa.Column('aggregated_accuracy', sa.Float(), nullable=True),
        sa.Column('aggregated_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'failed', name='fl_round_status'), nullable=False, server_default='pending'),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        
        # Differential Privacy Details
        sa.Column('privacy_epsilon', sa.Float(), nullable=True, comment='Privacy budget (epsilon) for differential privacy'),
        sa.Column('privacy_delta', sa.Float(), nullable=True, comment='Privacy parameter (delta) for differential privacy'),
        sa.Column('noise_stddev', sa.Float(), nullable=True, comment='Standard deviation of Gaussian noise added'),
        
        # Client Participation
        sa.Column('participating_clients', postgresql.JSONB(), nullable=True, comment='List of hospital IDs that participated'),
        sa.Column('failed_clients', postgresql.JSONB(), nullable=True, comment='List of clients that failed or timed out'),
        
        # Model & Training Details
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('aggregation_strategy', sa.String(50), nullable=False, server_default='FedAvg'),
        sa.Column('epoch_count', sa.Integer(), nullable=True, server_default=1),
        sa.Column('batch_size', sa.Integer(), nullable=True),
        
        # Error Tracking
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(), nullable=True),
        
        # Audit Trail
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Soft delete timestamp'),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('initiated_by', sa.String(255), nullable=True, comment='Admin user who initiated the round'),
        
        sa.PrimaryKeyConstraint('round_id', name='pk_fl_rounds'),
    )

    # Create indexes for optimal query performance
    op.create_index('idx_fl_rounds_round_number', 'fl_rounds', ['round_number'], unique=False)
    op.create_index('idx_fl_rounds_status', 'fl_rounds', ['status'], unique=False)
    op.create_index('idx_fl_rounds_created_at_desc', 'fl_rounds', ['created_at'], unique=False, postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_fl_rounds_deleted_at', 'fl_rounds', ['deleted_at'], unique=False)
    op.create_index('idx_fl_rounds_round_number_status', 'fl_rounds', ['round_number', 'status'], unique=False)

    # Add comments to the table
    op.execute("""
        COMMENT ON TABLE fl_rounds IS 'Federated Learning round metrics and metadata. Each row represents one protocol round where hospitals submit model updates.';
        COMMENT ON COLUMN fl_rounds.round_number IS 'Sequential round number (1-indexed)';
        COMMENT ON COLUMN fl_rounds.num_clients IS 'Number of hospital clients that contributed to this round';
        COMMENT ON COLUMN fl_rounds.aggregated_loss IS 'Global model loss after aggregation (FedAvg)';
        COMMENT ON COLUMN fl_rounds.aggregated_accuracy IS 'Global model accuracy after aggregation';
        COMMENT ON COLUMN fl_rounds.aggregated_metrics IS 'JSON object with additional metrics (precision, recall, AUC, etc.)';
        COMMENT ON COLUMN fl_rounds.status IS 'Current round status: pending -> in_progress -> completed/failed';
        COMMENT ON COLUMN fl_rounds.duration_seconds IS 'Total time to complete the round';
        COMMENT ON COLUMN fl_rounds.privacy_epsilon IS 'Epsilon parameter (lower = more private) for differential privacy';
        COMMENT ON COLUMN fl_rounds.privacy_delta IS 'Delta parameter for differential privacy';
        COMMENT ON COLUMN fl_rounds.participating_clients IS 'JSON array of hospital IDs like ["HOSPITAL_001", "HOSPITAL_002"]';
    """)


def downgrade() -> None:
    # Drop table
    op.drop_table('fl_rounds')
    
    # Drop enum type
    status_enum = postgresql.ENUM(
        'pending',
        'in_progress',
        'completed',
        'failed',
        name='fl_round_status'
    )
    status_enum.drop(op.get_bind(), checkfirst=True)
