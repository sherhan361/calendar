from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.responses import ApiException, api_exception_handler, validation_exception_handler
from app.api.routes import auth, bookings, event_types, me, schedules, share_links, slots
from app.core.config import settings


app = FastAPI(title="Calendar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["content-type", "authorization"],
)

app.add_exception_handler(ApiException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(schedules.router)
app.include_router(event_types.router)
app.include_router(share_links.router)
app.include_router(slots.router)
app.include_router(bookings.router)


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {"status": "ok"}
