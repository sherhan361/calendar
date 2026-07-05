from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import current_user
from app.api.responses import ApiException, success
from app.application import bookings as booking_use_cases
from app.db.models import Booking, User
from app.db.session import get_db
from app.schemas.contracts import BookingActionRequest, BookingStatus, CreateBookingRequest
from app.services.mappers import map_booking, map_booking_with_manage_token
from app.services.rate_limit import SlidingWindowRateLimiter, client_ip, get_booking_rate_limiter


router = APIRouter(tags=["Bookings"])


@router.post("/bookings", status_code=201)
def create_booking(
    body: CreateBookingRequest,
    request: Request,
    db: Session = Depends(get_db),
    rate_limiter: SlidingWindowRateLimiter = Depends(get_booking_rate_limiter),
) -> dict[str, object]:
    if not rate_limiter.allow(client_ip(request)):
        raise ApiException(429, "rate_limited", "Too many booking attempts. Please try again later.")
    return success(map_booking_with_manage_token(booking_use_cases.create_booking(db, body)))


@router.get("/bookings")
def list_bookings(
    status: BookingStatus | None = None,
    from_date: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    filters = [Booking.owner_id == user.id]
    if status is not None:
        filters.append(Booking.status == status.value)
    if from_date:
        filters.append(Booking.start >= _date_floor(from_date))
    if to:
        filters.append(Booking.start < _date_floor(to) + timedelta(days=1))

    bookings = db.scalars(select(Booking).where(*filters).order_by(Booking.start.asc())).all()
    return success({"items": [map_booking(booking) for booking in bookings]})


@router.get("/bookings/{booking_uid}")
def get_booking(
    booking_uid: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    booking = booking_use_cases.get_owned_booking(db, user.id, booking_uid)
    return success(map_booking(booking))


@router.post("/bookings/{booking_uid}/confirm")
def confirm_booking(
    booking_uid: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return success(map_booking(booking_use_cases.confirm_booking(db, user.id, booking_uid)))


@router.post("/bookings/{booking_uid}/decline")
def decline_booking(
    booking_uid: str,
    body: BookingActionRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return success(map_booking(booking_use_cases.decline_booking(db, user.id, booking_uid, body)))


@router.post("/bookings/{booking_uid}/cancel")
def cancel_booking(
    booking_uid: str,
    body: BookingActionRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return success(map_booking(booking_use_cases.cancel_booking(db, user.id, booking_uid, body)))


@router.post("/public/bookings/{booking_uid}/confirm", tags=["Public Bookings"])
def confirm_attendee(
    booking_uid: str,
    token: str,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return success(map_booking(booking_use_cases.confirm_attendee(db, booking_uid, token)))


@router.post("/public/bookings/{booking_uid}/cancel", tags=["Public Bookings"])
def cancel_attendee(
    booking_uid: str,
    body: BookingActionRequest,
    token: str,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return success(map_booking_with_manage_token(booking_use_cases.cancel_attendee(db, booking_uid, token, body)))


def _date_floor(raw: str) -> datetime:
    try:
        parsed = datetime.combine(datetime.strptime(raw, "%Y-%m-%d").date(), time.min, tzinfo=timezone.utc)
    except ValueError as exc:
        raise ApiException(400, "validation_error", "from and to must be local dates.") from exc
    return parsed
