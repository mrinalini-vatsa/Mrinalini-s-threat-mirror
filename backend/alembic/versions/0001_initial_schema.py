"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-01 20:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="severity"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)
    op.create_index(op.f("ix_alerts_ip_address"), "alerts", ["ip_address"], unique=False)
    op.create_index(op.f("ix_alerts_user_id"), "alerts", ["user_id"], unique=False)
    op.create_index(op.f("ix_alerts_event_type"), "alerts", ["event_type"], unique=False)
    op.create_index(op.f("ix_alerts_severity"), "alerts", ["severity"], unique=False)

    op.create_table(
        "enrichments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("reputation_score", sa.Integer(), nullable=False),
        sa.Column("country", sa.String(length=64), nullable=False),
        sa.Column("isp", sa.String(length=128), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_enrichments_alert_id"), "enrichments", ["alert_id"], unique=False)
    op.create_index(op.f("ix_enrichments_id"), "enrichments", ["id"], unique=False)

    op.create_table(
        "decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.Enum("ignore", "escalate", "block", name="decisiontype"), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_decisions_alert_id"), "decisions", ["alert_id"], unique=False)
    op.create_index(op.f("ix_decisions_id"), "decisions", ["id"], unique=False)

    op.create_table(
        "alert_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("state", sa.Enum("new", "enriched", "analyzed", "resolved", name="alertstatetype"), nullable=False),
        sa.Column("notes", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alert_states_alert_id"), "alert_states", ["alert_id"], unique=False)
    op.create_index(op.f("ix_alert_states_id"), "alert_states", ["id"], unique=False)

    op.create_table(
        "correlations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("related_alert_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["related_alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_correlations_alert_id"), "correlations", ["alert_id"], unique=False)
    op.create_index(op.f("ix_correlations_related_alert_id"), "correlations", ["related_alert_id"], unique=False)
    op.create_index(op.f("ix_correlations_id"), "correlations", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_correlations_id"), table_name="correlations")
    op.drop_index(op.f("ix_correlations_related_alert_id"), table_name="correlations")
    op.drop_index(op.f("ix_correlations_alert_id"), table_name="correlations")
    op.drop_table("correlations")
    op.drop_index(op.f("ix_alert_states_id"), table_name="alert_states")
    op.drop_index(op.f("ix_alert_states_alert_id"), table_name="alert_states")
    op.drop_table("alert_states")
    op.drop_index(op.f("ix_decisions_id"), table_name="decisions")
    op.drop_index(op.f("ix_decisions_alert_id"), table_name="decisions")
    op.drop_table("decisions")
    op.drop_index(op.f("ix_enrichments_id"), table_name="enrichments")
    op.drop_index(op.f("ix_enrichments_alert_id"), table_name="enrichments")
    op.drop_table("enrichments")
    op.drop_index(op.f("ix_alerts_severity"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_event_type"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_user_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_ip_address"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_id"), table_name="alerts")
    op.drop_table("alerts")
