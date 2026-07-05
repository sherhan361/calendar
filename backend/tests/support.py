from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient


@dataclass
class AuthenticatedClient:
    """TestClient в паре с JWT владельца и готовыми заголовками авторизации."""

    client: TestClient
    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}
