"""severity and correlation upgrade

Revision ID: 0002_severity_and_correlation_upgrade
Revises: 0001_initial_schema
Create Date: 2026-04-01 20:30:00
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_severity_and_correlation_upgrade"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Align severity enum values to explicit uppercase values.
    op.execute("ALTER TYPE severity RENAME TO severity_old")
    severity_new = sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="severity")
    severity_new.create(op.get_bind(), checkfirst=False)
    op.execute(
        """
        ALTER TABLE alerts
        ALTER COLUMN severity TYPE severity
        USING UPPER(severity::text)::severity
        """
    )
    op.execute("DROP TYPE severity_old")

    op.add_column(
        "correlations",
        sa.Column("correlation_strength", sa.Integer(), nullable=False, server_default="1"),
    )
    op.execute("ALTER TABLE correlations ALTER COLUMN correlation_strength DROP DEFAULT")


def downgrade() -> None:
    op.drop_column("correlations", "correlation_strength")

    op.execute("ALTER TYPE severity RENAME TO severity_new")
    severity_old = sa.Enum("low", "medium", "high", "critical", name="severity")
    severity_old.create(op.get_bind(), checkfirst=False)
    op.execute(
        """
        ALTER TABLE alerts
        ALTER COLUMN severity TYPE severity
        USING LOWER(severity::text)::severity
        """
    )
    op.execute("DROP TYPE severity_new")
