import contextlib

import asyncpg
from loguru import logger

import jouney.models  # noqa

from jouney.config import config


class AsyncDBProvider:
    def __init__(self, url):
        self._url = url
        self._pool = None

    @contextlib.asynccontextmanager
    async def _connect(self) -> asyncpg.Connection:
        if not self._pool:
            self._pool = await asyncpg.create_pool(self._url)
        async with self._pool.acquire() as conn:
            yield conn

    async def all(self, sql, *args, **kwargs) -> list[asyncpg.Record]:
        async with self._connect() as conn:
            logger.debug('Run request: {}', sql[:200])
            return list(await conn.fetch(sql, *args, **kwargs))

    async def execute(self, sql, *args):
        async with self._connect() as conn:
            await conn.execute(sql, *args)

    async def one(self, sql, *args, **kwargs) -> asyncpg.Record | None:
        async with self._connect() as conn:
            logger.debug('Run request: {}', sql[:200])
            return await conn.fetchrow(sql, *args, **kwargs)


_DB_SINGLETON = None


def get_async_db():
    global _DB_SINGLETON
    if _DB_SINGLETON is None:
        _DB_SINGLETON = AsyncDBProvider(config.DB_URL)
    return _DB_SINGLETON
