from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.security import hash_password  # noqa: E402
from app.db.models import Booking, EventType, Schedule, ShareLink, User  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.calendar import booking_url, default_availability, dumps_json, prepare_availability  # noqa: E402


def main() -> None:
    with SessionLocal() as db:
        db.execute(delete(Booking))
        db.execute(delete(ShareLink))
        db.execute(delete(EventType))
        db.execute(delete(Schedule))
        db.execute(delete(User))

        user = User(
            email="demo@example.com",
            username="demo",
            name="Dmitry Calendar",
            time_zone="Europe/Moscow",
            password_hash=hash_password("demo"),
        )
        db.add(user)
        db.flush()

        schedule = Schedule(
            owner_id=user.id,
            name="Working hours",
            time_zone="Europe/Moscow",
            is_default=True,
            availability_json=dumps_json(prepare_availability(default_availability())),
            overrides_json="[]",
        )
        db.add(schedule)
        db.flush()
        user.default_schedule_id = schedule.id

        product_discovery = EventType(
            owner_id=user.id,
            schedule_id=schedule.id,
            title="Product discovery",
            slug="product-discovery",
            description="A focused 30 minute call to align on goals, scope, and next steps.",
            duration_minutes=30,
            slot_interval_minutes=30,
            minimum_booking_notice_minutes=60,
            before_event_buffer_minutes=0,
            after_event_buffer_minutes=15,
            confirmation_policy_type="host",
            block_slot_before_confirmation=True,
            hidden=False,
            booking_url=booking_url(user.username, "product-discovery"),
        )
        db.add(product_discovery)
        db.flush()

        architecture_review = EventType(
            owner_id=user.id,
            schedule_id=schedule.id,
            title="Architecture review",
            slug="architecture-review",
            description="A longer technical review for backend design and integration tradeoffs.",
            duration_minutes=60,
            slot_interval_minutes=30,
            minimum_booking_notice_minutes=120,
            after_event_buffer_minutes=15,
            confirmation_policy_type="automatic",
            block_slot_before_confirmation=False,
            hidden=False,
            booking_url=booking_url(user.username, "architecture-review"),
        )
        db.add(architecture_review)

        share_token = "demo-product-link-2026"
        db.add(
            ShareLink(
                event_type_id=product_discovery.id,
                token=share_token,
                booking_url=booking_url(user.username, product_discovery.slug, share_token),
                recipient_email="guest@example.com",
                max_usage_count=5,
            )
        )

        tomorrow = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
        db.add(
            Booking(
                uid="booking_demo_pending",
                event_type_id=product_discovery.id,
                owner_id=user.id,
                title=product_discovery.title,
                description=product_discovery.description,
                status="pending_host",
                start=tomorrow,
                end=tomorrow + timedelta(minutes=product_discovery.duration_minutes),
                duration_minutes=product_discovery.duration_minutes,
                attendee_name="Alex Guest",
                attendee_email="alex@example.com",
                attendee_time_zone="Europe/Moscow",
                attendee_token="attendee_demo_pending_token",
                share_token=share_token,
            )
        )

        db.commit()
    print("Database seeded.")


if __name__ == "__main__":
    main()
