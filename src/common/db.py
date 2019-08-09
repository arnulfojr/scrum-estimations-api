"""Database singleton."""
from tortoise import Tortoise

from settings import db


async def start():
    await Tortoise.init(
        db_url=db.ENDPOINT,
        modules={
            'users': ['users.models'],
        }
    )


async def stop():
    await Tortoise.close_connections()
