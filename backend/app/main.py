from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import docx, health, openai_test, process, summarize
from .core.config import get_settings


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
    app.include_router(summarize.router, prefix='/api', tags=['summarize'])
    app.include_router(docx.router, prefix='/api', tags=['docx'])
    app.include_router(openai_test.router, prefix='/api', tags=['openai'])

    return app


app = create_app()

