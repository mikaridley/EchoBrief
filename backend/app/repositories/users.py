from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument


class UsersRepository:
    """Mongo access for the `users` collection (auth + quota)."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._users = db.get_collection('users')

    async def find_by_email(self, email: str) -> dict[str, Any] | None:
        return await self._users.find_one({'email': email})

    async def insert_google_user(
        self,
        *,
        email: str,
        name: str | None,
        picture: str | None,
        base_limit: int,
        now: int,
    ) -> None:
        await self._users.insert_one(
            {
                'email': email,
                'name': name,
                'picture': picture,
                'provider': 'google',
                'role': 'user',
                'enabled': False,
                'limits': {'summariesTotalLimit': base_limit, 'summariesTotalUsed': 0},
                'createdAt': now,
                'lastLoginAt': now,
            }
        )

    async def update_google_profile_on_login(
        self,
        *,
        user_id: Any,
        name: str | None,
        picture: str | None,
        now: int,
        base_limit: int,
    ) -> None:
        await self._users.update_one(
            {'_id': user_id},
            {
                '$set': {'name': name, 'picture': picture, 'lastLoginAt': now},
                '$setOnInsert': {
                    'createdAt': now,
                    'provider': 'google',
                    'role': 'user',
                    'enabled': False,
                    'limits': {'summariesTotalLimit': base_limit, 'summariesTotalUsed': 0},
                },
            },
            upsert=True,
        )

    async def try_increment_summary_usage(self, email: str) -> dict[str, Any] | None:
        return await self._users.find_one_and_update(
            {
                'email': email,
                'enabled': True,
                '$expr': {'$lt': ['$limits.summariesTotalUsed', '$limits.summariesTotalLimit']},
            },
            {'$inc': {'limits.summariesTotalUsed': 1}},
            return_document=ReturnDocument.AFTER,
        )
