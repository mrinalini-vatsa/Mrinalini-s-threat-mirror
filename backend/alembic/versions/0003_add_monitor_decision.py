"""add monitor decision type

Revision ID: 0003_add_monitor_decision
Revises: 0002_severity_and_correlation_upgrade
Create Date: 2026-04-01 22:00:00
"""
from alembic import op


revision = "0003_add_monitor_decision"
down_revision = "0002_severity_and_correlation_upgrade"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $outer$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = 'decisiontype' AND e.enumlabel = 'monitor'
                ) THEN
                    ALTER TYPE decisiontype ADD VALUE 'monitor';
                END IF;
            END
            $outer$;
            """
        )


def downgrade() -> None:
    pass
