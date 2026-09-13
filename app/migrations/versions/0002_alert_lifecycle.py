"""Add persisted alert lifecycle state."""

from alembic import op

revision = "0002_alert_lifecycle"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS FRAUDSHIELD.FRAUD_ALERTS (
            TXN_ID DECIMAL(18, 0) PRIMARY KEY,
            LIFECYCLE_STATUS VARCHAR(20) DEFAULT 'NEW',
            UPDATED_AT TIMESTAMP,
            ACKNOWLEDGED_BY VARCHAR(100),
            RESOLVED_AT TIMESTAMP
        )
    """)
    sql_file = __file__.rsplit("/migrations/", 1)[0] + "/fraudshield/schema/fraud_views.sql"
    with open(sql_file) as view_file:
        op.execute(view_file.read())


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS FRAUDSHIELD.FRAUD_SCORES")
    op.execute("DROP TABLE IF EXISTS FRAUDSHIELD.FRAUD_ALERTS")