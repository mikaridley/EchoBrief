from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import get_settings


def create_mongo_client() -> AsyncIOMotorClient:
    settings = get_settings()
    if not settings.mongo_uri:
        raise RuntimeError('Missing MONGO_URI. Set it in backend/.env')
    return AsyncIOMotorClient(settings.mongo_uri)


def get_db_from_app(app) -> AsyncIOMotorDatabase:
    db = getattr(app.state, 'mongo_db', None)
    if db is None:
        raise RuntimeError('Mongo DB is not initialized on app.state')
    return db

