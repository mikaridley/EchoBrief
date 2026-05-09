from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import auth, docx, health, openai_test, process, summarize
from .core.config import get_settings
from .core.db import create_mongo_client


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.auth_enabled:
            if not settings.mongo_uri:
                raise RuntimeError('AUTH_ENABLED=1 requires MONGO_URI')
            if not settings.google_client_id:
                raise RuntimeError('AUTH_ENABLED=1 requires GOOGLE_CLIENT_ID')

        if settings.mongo_uri:
            client = create_mongo_client()
            app.state.mongo_client = client
            app.state.mongo_db = client[settings.mongo_db_name]
        yield
        client = getattr(app.state, 'mongo_client', None)
        if client is not None:
            client.close()

    app = FastAPI(title='EchoBrief API', version='0.1.0', lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.include_router(health.router, prefix='/api', tags=['health'])
    app.include_router(auth.router, prefix='/api', tags=['auth'])
    app.include_router(process.router, prefix='/api', tags=['process'])
    app.include_router(summarize.router, prefix='/api', tags=['summarize'])
    app.include_router(docx.router, prefix='/api', tags=['docx'])
    app.include_router(openai_test.router, prefix='/api', tags=['openai'])

    return app


app = create_app()

