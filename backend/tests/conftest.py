from __future__ import annotations

from collections.abc import Iterator

import pytest

from app.services.rate_limit import booking_rate_limiter


@pytest.fixture(autouse=True)
def reset_booking_rate_limiter() -> Iterator[None]:
    booking_rate_limiter.reset()
    yield
    booking_rate_limiter.reset()
