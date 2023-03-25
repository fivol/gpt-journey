import asyncpg

from jouney.db import AsyncDBProvider


class ChatDB:
    def __init__(self, chat_id: int, db: AsyncDBProvider):
        self._db = db
        self._chat_id = chat_id


class StoriesDB(ChatDB):
    async def create(self):
        response = await self._db.one(
            "INSERT INTO stories (user_id) VALUES ($1) returning *",
            self._chat_id
        )
        return response["id"]

    async def add_text(self, story_id: int, text: str, img: str) -> int:
        response = await self._db.one(
            "INSERT INTO story_items (story_id, text, img) VALUES ($1, $2, $3) returning *",
            story_id, text, img
        )
        return response["id"]

    async def update_option(self, story_item_id: int, option: int):
        return await self._db.execute(
            "UPDATE story_items SET option = $1 WHERE id = $2",
            option, story_item_id
        )


class UserDB(ChatDB):

    @property
    def stories(self) -> StoriesDB:
        return StoriesDB(self._chat_id, self._db)

    async def create(self, name: str, username: str):
        try:
            return await self._db.execute(
                'INSERT INTO users (id, name, username) VALUES ($1, $2, $3)',
                self._chat_id, name, username
            )
        except asyncpg.UniqueViolationError:
            pass

    async def get_user(self):
        return await self._db.one(
            'SELECT * FROM users WHERE user_id = $1',
            self._chat_id
        )


