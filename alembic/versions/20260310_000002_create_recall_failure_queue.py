"""create recall failure queue table"""

from alembic import op
import sqlalchemy as sa


revision = "20260310_000002"
down_revision = "20260310_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recall_failure_queue",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("email_address", sa.String(length=320), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("join_url", sa.String(length=2048), nullable=False),
        sa.Column("join_at", sa.String(length=64), nullable=True),
        sa.Column("bot_ids", sa.JSON(), nullable=False),
        sa.Column("error_type", sa.String(length=128), nullable=False),
        sa.Column("error_message", sa.String(length=2048), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recall_failure_queue_status",
        "recall_failure_queue",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_recall_failure_queue_email_address",
        "recall_failure_queue",
        ["email_address"],
        unique=False,
    )
    op.create_index(
        "ix_recall_failure_queue_join_url",
        "recall_failure_queue",
        ["join_url"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_recall_failure_queue_join_url", table_name="recall_failure_queue")
    op.drop_index("ix_recall_failure_queue_email_address", table_name="recall_failure_queue")
    op.drop_index("ix_recall_failure_queue_status", table_name="recall_failure_queue")
    op.drop_table("recall_failure_queue")