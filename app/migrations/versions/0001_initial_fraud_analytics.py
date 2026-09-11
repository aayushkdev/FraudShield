"""Create the transaction model and Exasol fraud analytics view."""

from alembic import op

from fraudshield.models.transaction import Transaction

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

SQL_FILE = __file__.rsplit("/migrations/", 1)[0] + "/fraudshield/schema/fraud_views.sql"


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS FRAUDSHIELD")
    Transaction.__table__.create(bind=op.get_bind(), checkfirst=True)
    with open(SQL_FILE) as view_file:
        op.execute(view_file.read())


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS FRAUDSHIELD.FRAUD_SCORES")
    op.execute("DROP TABLE IF EXISTS FRAUDSHIELD.TRANSACTIONS")
