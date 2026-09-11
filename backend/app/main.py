"""FastAPI application.

All learner routes live under /api/v1 and are served same-origin behind a
reverse proxy in both development and deployment.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import routes_assessment, routes_core, routes_lab, routes_tutor
from app.config import get_settings
from app.quantum.errors import CircuitRejected

API_PREFIX = "/api/v1"

logger = logging.getLogger("app")

DESCRIPTION = """
Backend for the Quantum Learning Laboratory.

The quantum engine computes, the authored evaluator grades, and the tutor
teaches. Private rubrics and answer keys are never returned by any route in
this contract.
"""


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Quantum Learning Laboratory API",
        version="0.1.0",
        description=DESCRIPTION.strip(),
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
    )

    @app.exception_handler(CircuitRejected)
    async def circuit_rejected_handler(_request: Request, error: CircuitRejected) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": {"code": error.reason_code, "message": error.message}},
        )

    for router in (
        routes_core.router,
        routes_lab.router,
        routes_assessment.router,
        routes_tutor.router,
    ):
        app.include_router(router, prefix=API_PREFIX)

    @app.get("/health/live", include_in_schema=False)
    def health_live_alias() -> dict[str, str]:
        return {"status": "live"}

    logger.info("starting app env=%s tutor_provider=%s", settings.app_env, settings.tutor_provider)
    return app


app = create_app()


def openapi_document() -> dict[str, Any]:
    """The deterministic contract export used by contracts/openapi.json."""
    return create_app().openapi()
