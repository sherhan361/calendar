from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=2048), nullable=True),
        sa.Column("time_zone", sa.String(length=128), nullable=False),
        sa.Column("default_schedule_id", sa.String(length=36), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "schedules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("time_zone", sa.String(length=128), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("availability_json", sa.Text(), nullable=False),
        sa.Column("overrides_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_schedules_owner_id", "schedules", ["owner_id"])

    op.create_table(
        "event_types",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("schedule_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("slot_interval_minutes", sa.Integer(), nullable=True),
        sa.Column("minimum_booking_notice_minutes", sa.Integer(), nullable=True),
        sa.Column("before_event_buffer_minutes", sa.Integer(), nullable=True),
        sa.Column("after_event_buffer_minutes", sa.Integer(), nullable=True),
        sa.Column("booking_window_json", sa.Text(), nullable=True),
        sa.Column("confirmation_policy_type", sa.String(length=32), nullable=False),
        sa.Column("block_slot_before_confirmation", sa.Boolean(), nullable=False),
        sa.Column("hidden", sa.Boolean(), nullable=False),
        sa.Column("booking_url", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("duration_minutes > 0", name="ck_event_types_duration_positive"),
        sa.CheckConstraint(
            "slot_interval_minutes IS NULL OR slot_interval_minutes > 0",
            name="ck_event_types_slot_interval_positive",
        ),
        sa.CheckConstraint(
            "minimum_booking_notice_minutes IS NULL OR minimum_booking_notice_minutes >= 0",
            name="ck_event_types_minimum_notice_non_negative",
        ),
        sa.CheckConstraint(
            "before_event_buffer_minutes IS NULL OR before_event_buffer_minutes >= 0",
            name="ck_event_types_before_buffer_non_negative",
        ),
        sa.CheckConstraint(
            "after_event_buffer_minutes IS NULL OR after_event_buffer_minutes >= 0",
            name="ck_event_types_after_buffer_non_negative",
        ),
        sa.CheckConstraint(
            "confirmation_policy_type IN ('automatic', 'host', 'attendee')",
            name="ck_event_types_confirmation_policy",
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "slug", name="uq_event_types_owner_slug"),
    )
    op.create_index("ix_event_types_schedule_id", "event_types", ["schedule_id"])

    op.create_table(
        "share_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type_id", sa.String(length=36), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("booking_url", sa.String(length=512), nullable=False),
        sa.Column("recipient_email", sa.String(length=320), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_usage_count", sa.Integer(), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("max_usage_count IS NULL OR max_usage_count > 0", name="ck_share_links_max_usage_positive"),
        sa.CheckConstraint("usage_count >= 0", name="ck_share_links_usage_non_negative"),
        sa.ForeignKeyConstraint(["event_type_id"], ["event_types.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_share_links_event_type_id", "share_links", ["event_type_id"])
    op.create_index("ix_share_links_token", "share_links", ["token"], unique=True)

    op.create_table(
        "bookings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("uid", sa.String(length=64), nullable=False),
        sa.Column("event_type_id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("attendee_name", sa.String(length=255), nullable=False),
        sa.Column("attendee_email", sa.String(length=320), nullable=False),
        sa.Column("attendee_time_zone", sa.String(length=128), nullable=False),
        sa.Column("attendee_token", sa.String(length=128), nullable=False),
        sa.Column("attendee_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("share_token", sa.String(length=128), nullable=True),
        sa.Column("meeting_url", sa.String(length=2048), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending_host', 'pending_attendee', 'confirmed', 'declined', 'cancelled')",
            name="ck_bookings_status",
        ),
        sa.CheckConstraint("duration_minutes > 0", name="ck_bookings_duration_positive"),
        sa.ForeignKeyConstraint(["event_type_id"], ["event_types.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bookings_event_type_start", "bookings", ["event_type_id", "start"])
    op.create_index("ix_bookings_owner_status", "bookings", ["owner_id", "status"])
    op.create_index("ix_bookings_uid", "bookings", ["uid"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_bookings_uid", table_name="bookings")
    op.drop_index("ix_bookings_owner_status", table_name="bookings")
    op.drop_index("ix_bookings_event_type_start", table_name="bookings")
    op.drop_table("bookings")
    op.drop_index("ix_share_links_token", table_name="share_links")
    op.drop_index("ix_share_links_event_type_id", table_name="share_links")
    op.drop_table("share_links")
    op.drop_index("ix_event_types_schedule_id", table_name="event_types")
    op.drop_table("event_types")
    op.drop_index("ix_schedules_owner_id", table_name="schedules")
    op.drop_table("schedules")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
