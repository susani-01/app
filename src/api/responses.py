from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from src.api.schemas import ApiResponse


def success_response(data: Any, message: str | None = None) -> JSONResponse:
    body = ApiResponse(status="success", data=data, message=message)
    return JSONResponse(status_code=200, content=body.model_dump(mode="json"))


def failure_response(message: str, data: Any | None = None) -> JSONResponse:
    body = ApiResponse(status="failure", data=data, message=message)
    return JSONResponse(status_code=200, content=body.model_dump(mode="json"))
