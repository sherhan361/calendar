from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_booking_idempotency"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


_ACTIVE_SLOT_WHERE = "status IN ('pending_host', 'pending_attendee', 'confirmed')"


def upgrade() -> None:
    op.add_column("bookings", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.create_index(
        "uq_bookings_event_type_idempotency_key",
        "bookings",
        ["event_type_id", "idempotency_key"],
        unique=True,
    )
    op.create_index(
        "uq_bookings_active_slot",
        "bookings",
        ["event_type_id", "start"],
        unique=True,
        sqlite_where=sa.text(_ACTIVE_SLOT_WHERE),
        postgresql_where=sa.text(_ACTIVE_SLOT_WHERE),
    )


def downgrade() -> None:
    op.drop_index("uq_bookings_active_slot", table_name="bookings")
    op.drop_index("uq_bookings_event_type_idempotency_key", table_name="bookings")
    op.drop_column("bookings", "idempotency_key")
