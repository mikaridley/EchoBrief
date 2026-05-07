from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import docx, health, process
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title='EchoBrief API', version='0.1.0')

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.include_router(health.router, prefix='/api', tags=['health'])
    app.include_router(process.router, prefix='/api', tags=['process'])
    app.include_router(docx.router, prefix='/api', tags=['docx'])

    return app


app = create_app()

