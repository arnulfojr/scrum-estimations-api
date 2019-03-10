"""Database singleton."""
import peewee_async

from settings import db


database = peewee_async.MySQLDatabase(db.DATABASE,
                                      host=db.HOST,
                                      port=db.PORT,
                                      user=db.USER,
                                      password=db.PASSWORD)


manager = peewee_async.Manager(database)


class MixinModel:
    """MixinModel that contains essential manipulation."""

    @classmethod
    async def get(cls, id):
        try:
            model = await manager.get(cls, id=id)
        except cls.DoesNotExist:
            return None
        else:
            return model

    async def put(self, only=None):
        """Persists the current state of the instance."""
        await manager.update(self, only=only)

    async def remove(self):
        """Remove the user from the database."""
        await manager.delete(self)
