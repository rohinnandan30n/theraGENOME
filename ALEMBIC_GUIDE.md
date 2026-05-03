# Alembic Migration Guide for TheraGenome

## Quick Start

### Initial Setup (First Time)

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure database connection
cp .env.example .env
# Edit .env with your PostgreSQL credentials:
# DATABASE_URL=postgresql://user:password@localhost:5432/thergenome_dev

# 4. Apply all pending migrations
alembic upgrade head
```

### Verify Installation

```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Check database schema
psql -U <user> -d thergenome_dev -c "\d patients"
```

---

## Common Alembic Commands

### View Migrations

```bash
# Current migration version
alembic current

# Full history (all migrations)
alembic history --verbose

# History with range
alembic history -r <start>:<end>
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +3

# Apply to specific revision
alembic upgrade 001_create_patients_table
```

### Rollback Migrations

```bash
# Rollback last migration
alembic downgrade -1

# Rollback multiple migrations
alembic downgrade -10

# Rollback to specific revision
alembic downgrade 001_create_patients_table
```

### Create New Migrations

```bash
# Manual migration (recommended)
alembic revision -m "descriptive migration name"
# Creates: alembic/versions/###_descriptive_migration_name.py

# Auto-generate from ORM models (if using declarative models)
alembic revision --autogenerate -m "auto migration name"
```

---

## Creating a New Migration (Step-by-Step)

### Scenario: Add email column to patients table

**Step 1: Create migration file**
```bash
alembic revision -m "add_email_to_patients"
# Creates: alembic/versions/002_add_email_to_patients.py
```

**Step 2: Edit the migration file**

File: `alembic/versions/002_add_email_to_patients.py`

```python
"""Add email column to patients table

Revision ID: 002_add_email_to_patients
Revises: 001_create_patients_table
Create Date: 2026-04-01 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_add_email_to_patients"
down_revision = "001_create_patients_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add email column to patients table"""
    op.add_column(
        "patients",
        sa.Column(
            "email",
            sa.String(255),
            nullable=True,
            comment="Patient email address"
        ),
    )
    # Add unique index for email lookups
    op.create_index(
        "idx_patients_email",
        "patients",
        ["email"],
        unique=True,
    )


def downgrade() -> None:
    """Rollback: Remove email column"""
    op.drop_index("idx_patients_email", table_name="patients")
    op.drop_column("patients", "email")
```

**Step 3: Test the migration**
```bash
# Upgrade to new migration
alembic upgrade head

# Test that schema is correct
psql -U <user> -d thergenome_dev -c "\d patients"

# Test downgrade
alembic downgrade -1
psql -U <user> -d thergenome_dev -c "\d patients"

# Re-apply upgrade
alembic upgrade head
```

**Step 4: Commit and share**
```bash
git add alembic/versions/002_add_email_to_patients.py
git commit -m "feat(schema): add email column to patients table"
git push origin main
```

---

## Team Synchronization Workflow

### When You Pull New Migrations

```bash
# 1. Update local code
git pull origin main

# 2. Check what migrations are pending
alembic current
alembic upgrade --sql head  # Preview SQL (don't apply yet)

# 3. Apply new migrations
alembic upgrade head

# 4. Verify schema updated
alembic current
psql -U <user> -d thergenome_dev -c "\d"
```

### When You're Publishing New Migrations

```bash
# 1. Create and test migration locally
alembic revision -m "your_migration_name"
# Edit alembic/versions/###_your_migration_name.py

# 2. Test locally
alembic upgrade head
# Test application code with new schema
alembic downgrade -1
alembic upgrade head

# 3. Export updated schema
python scripts/export_schema.py
# Updates: schemas/patient_schema.sql

# 4. Commit everything
git add alembic/versions/###_your_migration_name.py
git add schemas/patient_schema.sql
git commit -m "feat(schema): your migration description"

# 5. Notify team
# Create PR or slack notification with migration details
```

---

## Migration Patterns

### Adding a Column

```python
def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column("new_column", sa.String(100), nullable=True),
    )

def downgrade() -> None:
    op.drop_column("patients", "new_column")
```

### Removing a Column

```python
def upgrade() -> None:
    op.drop_column("patients", "obsolete_column")

def downgrade() -> None:
    op.add_column(
        "patients",
        sa.Column("obsolete_column", sa.String(100), nullable=True),
    )
```

### Adding an Index

```python
def upgrade() -> None:
    op.create_index(
        "idx_patients_new_field",
        "patients",
        ["new_field"],
    )

def downgrade() -> None:
    op.drop_index("idx_patients_new_field", table_name="patients")
```

### Adding a Constraint

```python
def upgrade() -> None:
    op.create_check_constraint(
        "ck_patients_age_valid",
        "patients",
        "EXTRACT(YEAR FROM AGE(NOW(), date_of_birth)) BETWEEN 0 AND 150",
    )

def downgrade() -> None:
    op.drop_constraint("ck_patients_age_valid", "patients", type_="check")
```

### Creating a New Table

```python
def upgrade() -> None:
    op.create_table(
        "medical_records",
        sa.Column("record_id", sa.UUID(), server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("record_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("record_type", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("record_id"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.patient_id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_medical_records_patient_id", "medical_records", ["patient_id"])

def downgrade() -> None:
    op.drop_table("medical_records")
```

---

## Troubleshooting

### Migration Won't Apply

```bash
# Check current status
alembic current

# Get more details about the error
alembic upgrade head --sql  # See what SQL will be executed

# Check database connectivity
python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://...'); print('Connected')"
```

### Migration Failed Midway

```bash
# Check database state
alembic current
alembic history

# Manually fix database if needed
psql -U <user> -d thergenome_dev

# Retry migration
alembic upgrade head
```

### Need to Modify Last Migration

```bash
# Option 1: Downgrade and redo
alembic downgrade -1
# Edit the migration file
alembic upgrade head

# Option 2: Create a fixup migration (preferred for shared code)
alembic revision -m "fix_previous_migration"
# Write the fix in the new migration
alembic upgrade head
```

### Schema Out of Sync with HEAD

```bash
# Reset to a known good state
alembic downgrade -99  # Go back to beginning
alembic upgrade head   # Re-apply all

# Or check what's different
alembic current
alembic upgrade --sql head
```

---

## Best Practices

### ✅ DO

- **Small, focused migrations** - One logical change per migration
- **Descriptive names** - Use business language in migration names
- **Test both upgrade and downgrade** - Ensure reversibility
- **Test with real data** - Catch edge cases before deployment
- **Export schema after changes** - Keep patient_schema.sql updated
- **Document breaking changes** - Include notes for team
- **Check constraints** - Add NOT NULL checks and foreign keys as needed

### ❌ DON'T

- **Complex logic in migrations** - Keep Python code minimal
- **Mix schema and data changes** - Separate concerns
- **Modify existing migrations** - Always create new ones
- **Skip reversibility testing** - Assume downgrade works
- **Auto-generate without review** - Always review generated SQL
- **Rush deployment** - Test thoroughly first

---

## Migration Checklist

Before committing a new migration:

- [ ] Migration file created: `alembic/versions/###_<name>.py`
- [ ] Upgrade function tested: `alembic upgrade head`
- [ ] Downgrade function tested: `alembic downgrade -1`
- [ ] Re-upgrade tested: `alembic upgrade head`
- [ ] Schema export updated: `python scripts/export_schema.py`
- [ ] No raw SQL hardcoding - only SQLAlchemy operations
- [ ] Comments document what the migration does
- [ ] Team notified of breaking changes (if any)
- [ ] Revision ID unique and sequential
- [ ] Down revision correctly references previous migration

---

## Performance Considerations

### For Large Tables

```python
# Create index WITHOUT BLOCKING table (takes longer but safe)
def upgrade() -> None:
    op.create_index(
        "idx_patients_email",
        "patients",
        ["email"],
        postgresql_concurrently=True,  # PostgreSQL: avoid table locks
    )
```

### Renaming Columns

```python
# Option 1: Add new, copy data, drop old (safe, but slower)
def upgrade() -> None:
    op.add_column("patients", sa.Column("email_new", sa.String(255)))
    op.execute("UPDATE patients SET email_new = email_address")
    op.drop_column("patients", "email_address")
    op.rename_table("email_new", "email")  # Not recommended directly

# Option 2: Rename directly (fastest, but risky)
def upgrade() -> None:
    op.alter_column("patients", "email_address", new_column_name="email")
```

---

## Integration with Development Workflow

### Git Hooks (Optional)

Create `.git/hooks/pre-commit` to validate migrations:

```bash
#!/bin/bash
# Check for migration files with syntax errors
for file in alembic/versions/*.py; do
    python -m py_compile "$file" || exit 1
done
exit 0
```

### CI/CD Integration (GitHub Actions Example)

```yaml
# .github/workflows/migrate.yml
name: Test Migrations
on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_HOST_AUTH_METHOD: trust
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v3
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: alembic upgrade head
      - run: python scripts/seed_patients.py 10
```

---

## Resources

- **Alembic Docs:** https://alembic.sqlalchemy.org/
- **SQLAlchemy Operations:** https://alembic.sqlalchemy.org/en/latest/ops.html
- **PostgreSQL Extensions:** https://www.postgresql.org/docs/current/sql-createextension.html

---

**Last Updated:** March 31, 2026  
**Maintained By:** Database Architecture Team
