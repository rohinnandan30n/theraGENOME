"""Create core patients table

Revision ID: 001_create_patients_table
Revises: 
Create Date: 2026-03-31

This migration creates the foundational patients table with UUID primary key,
demographic fields, and soft delete support. Indexes are added for query optimization.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_create_patients_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create patients table with core demographics and audit columns"""
    op.create_table(
        "patients",
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            nullable=False,
            comment="Unique patient identifier (UUID v4)",
        ),
        sa.Column(
            "first_name",
            sa.String(255),
            nullable=False,
            comment="Patient's first name",
        ),
        sa.Column(
            "last_name",
            sa.String(255),
            nullable=False,
            comment="Patient's last name",
        ),
        sa.Column(
            "date_of_birth",
            sa.Date(),
            nullable=False,
            comment="Patient's date of birth",
        ),
        sa.Column(
            "sex",
            sa.String(20),
            nullable=True,
            comment="Biological sex (M/F/Other/Prefer not to say)",
        ),
        sa.Column(
            "ethnicity",
            sa.String(255),
            nullable=True,
            comment="Patient's ethnicity",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment="Last update timestamp",
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Soft delete timestamp (NULL if active)",
        ),
        sa.PrimaryKeyConstraint("patient_id", name="pk_patients_patient_id"),
        comment="Core patient demographics and identity table - HIPAA sensitive",
    )

    # Create indexes for commonly queried fields
    op.create_index(
        "idx_patients_patient_id",
        "patients",
        ["patient_id"],
        unique=True,
    )
    op.create_index(
        "idx_patients_date_of_birth",
        "patients",
        ["date_of_birth"],
    )
    op.create_index(
        "idx_patients_deleted_at",
        "patients",
        ["deleted_at"],
        comment="Index for soft delete queries (find active patients)",
    )
    op.create_index(
        "idx_patients_created_at",
        "patients",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop patients table and all indexes"""
    op.drop_index("idx_patients_created_at", table_name="patients")
    op.drop_index("idx_patients_deleted_at", table_name="patients")
    op.drop_index("idx_patients_date_of_birth", table_name="patients")
    op.drop_index("idx_patients_patient_id", table_name="patients")
    op.drop_table("patients")
