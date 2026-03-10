"""add end_at column to meeting_invite"""

from alembic import op
import sqlalchemy as sa


revision = "20260310_000004"
down_revision = "20260310_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "meeting_invite",
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("meeting_invite", "end_at")
