from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.responses import failure_response
from src.api.routes.classification import router as classification_router
from src.api.routes.item import router as item_router
from src.api.routes.system import router as system_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Construction Standard Price API",
        description=(
            "Reference API for construction quantity items and standard market prices."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        messages = [
            f"{'.'.join(str(part) for part in error.get('loc', []))}: {error.get('msg')}"
            for error in exc.errors()
        ]
        return failure_response("; ".join(messages))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return failure_response(str(exc))

    app.include_router(system_router)
    app.include_router(classification_router)
    app.include_router(item_router)
    return app


app = create_app()
