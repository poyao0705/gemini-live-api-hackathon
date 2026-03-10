"""create meeting invite table"""

from alembic import op
import sqlalchemy as sa


revision = "20260310_000003"
down_revision = "20260310_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meeting_invite",
        sa.Column("gmail_message_id", sa.String(length=64), nullable=False),
        sa.Column("email_address", sa.String(length=320), nullable=False),
        sa.Column("gmail_thread_id", sa.String(length=64), nullable=True),
        sa.Column("gmail_history_id", sa.String(length=64), nullable=True),
        sa.Column("sender", sa.String(length=512), nullable=True),
        sa.Column("recipient", sa.String(length=512), nullable=True),
        sa.Column("subject", sa.String(length=1024), nullable=True),
        sa.Column("message_date", sa.String(length=256), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("calendar_event_id", sa.String(length=512), nullable=True),
        sa.Column("join_url", sa.String(length=2048), nullable=True),
        sa.Column("join_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meeting_status", sa.String(length=32), nullable=False),
        sa.Column("email_event_type", sa.String(length=32), nullable=False),
        sa.Column("is_canceled", sa.Boolean(), nullable=False),
        sa.Column("meeting_details_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("gmail_message_id"),
    )
    op.create_index("ix_meeting_invite_email_address", "meeting_invite", ["email_address"], unique=False)
    op.create_index("ix_meeting_invite_gmail_thread_id", "meeting_invite", ["gmail_thread_id"], unique=False)
    op.create_index("ix_meeting_invite_gmail_history_id", "meeting_invite", ["gmail_history_id"], unique=False)
    op.create_index("ix_meeting_invite_calendar_event_id", "meeting_invite", ["calendar_event_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_meeting_invite_calendar_event_id", table_name="meeting_invite")
    op.drop_index("ix_meeting_invite_gmail_history_id", table_name="meeting_invite")
    op.drop_index("ix_meeting_invite_gmail_thread_id", table_name="meeting_invite")
    op.drop_index("ix_meeting_invite_email_address", table_name="meeting_invite")
    op.drop_table("meeting_invite")