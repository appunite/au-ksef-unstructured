from fastapi import FastAPI

from src.app.routes import extract, health


def create_app() -> FastAPI:
    app = FastAPI(
        title="au-ksef-unstructured",
        description="Extract structured invoice data from PDFs",
        version="0.1.0",
    )
    app.include_router(health.router)
    app.include_router(extract.router)
    return app


app = create_app()
