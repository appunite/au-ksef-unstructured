import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.app.config import get_settings
from src.app.routes import extract, health


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = FastAPI(
        title="au-ksef-unstructured",
        description="Extract structured invoice data from PDFs",
        version="0.1.0",
    )
    app.include_router(health.router)
    app.include_router(extract.router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        code = {401: "authentication_error", 403: "authentication_error"}.get(
            exc.status_code, "validation_error"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": {"code": code, "message": str(exc.detail)}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        messages = "; ".join(e["msg"] for e in exc.errors())
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "validation_error", "message": messages},
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {"code": "internal_error", "message": "Internal server error"},
            },
        )

    return app


app = create_app()
