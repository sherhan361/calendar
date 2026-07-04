from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiException(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: list[dict[str, str]] | None = None) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def success(data: object) -> dict[str, object]:
    return {"status": "success", "data": data}


def error_payload(code: str, message: str, details: list[dict[str, str]] | None = None) -> dict[str, object]:
    error: dict[str, object] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"status": "error", "error": error}


async def api_exception_handler(_: Request, exc: ApiException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code, exc.message, exc.details),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", []) if part not in {"body", "query", "path"}]
        details.append({"field": ".".join(location), "message": error.get("msg", "Invalid value")})
    return JSONResponse(
        status_code=400,
        content=error_payload("validation_error", "Request validation failed.", details),
    )
