"""Organization models."""
from datetime import datetime
from uuid import uuid4

import peewee

from common.db import database
from common.db import manager
from common.db import MixinModel


class Organization(MixinModel, peewee.Model):
    """Organizations model."""
    id = peewee.UUIDField(primary_key=True, default=uuid4)

    name = peewee.CharField(null=False)

    registered_on = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        db_table = 'organizations'

    @classmethod
    async def create_from(cls, data: dict):
        name = data.get('name')

        organization = await manager.create(cls, name=name)
        return organization

    def dict_dump(self) -> dict:
        dump = {
            'id': str(self.id),
            'name': self.name,
        }

        if self.users:
            dump['users'] = [u.dict_dump() for u in self.users]

        return dump
