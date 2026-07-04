from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = field(default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"])


def _default_database_url() -> str:
    db_path = BACKEND_DIR / "data" / "calendar.sqlite"
    return f"sqlite:///{db_path}"


def _cors_origins() -> list[str]:
    raw = os.getenv("CALENDAR_CORS_ORIGINS")
    if not raw:
        return [
            *(f"http://127.0.0.1:{port}" for port in range(5173, 5180)),
            *(f"http://localhost:{port}" for port in range(5173, 5180)),
        ]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


settings = Settings(
    database_url=os.getenv("CALENDAR_DATABASE_URL", _default_database_url()),
    jwt_secret=os.getenv("CALENDAR_JWT_SECRET", "dev-calendar-secret-change-me-at-least-32-bytes"),
    access_token_expire_minutes=int(os.getenv("CALENDAR_ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))),
    cors_origins=_cors_origins(),
)
