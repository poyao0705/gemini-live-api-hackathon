"""create gmail history state table"""

from alembic import op
import sqlalchemy as sa


revision = "20260310_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gmail_history_state",
        sa.Column("email_address", sa.String(length=320), nullable=False),
        sa.Column("last_history_id", sa.String(length=64), nullable=False),
        sa.Column("last_sync_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("watch_expiration", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("reset_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("email_address"),
    )
    op.create_index(
        "ix_gmail_history_state_last_history_id",
        "gmail_history_state",
        ["last_history_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_gmail_history_state_last_history_id", table_name="gmail_history_state")
    op.drop_table("gmail_history_state")