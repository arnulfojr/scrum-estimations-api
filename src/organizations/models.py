"""Organization models."""
from datetime import datetime
from typing import List
from uuid import uuid4

import peewee

from common.db import database

from .exceptions import NotFound


class Organization(peewee.Model):
    """Organizations model.

    Receives the backref from the User class as 'users'
    """
    id = peewee.UUIDField(primary_key=True, default=uuid4)

    name = peewee.CharField(null=False, index=True)

    registered_on = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        table_name = 'organizations'

    @classmethod
    def lookup(cls, identifier) -> 'Organization':
        query = cls.select().where(cls.id == identifier)
        try:
            instance = query.get()
        except cls.DoesNotExist as e:
            raise NotFound(f'Organization with ID {identifier} was not found', e) from e
        else:
            return instance

    @classmethod
    def search(cls, name: str) -> List['Organization']:
        query = cls.select().where(cls.name.contains(name))
        return list(query)

    @classmethod
    def create_from(cls, data: dict) -> 'Organization':
        name = data.get('name')

        with database.atomic() as txn:
            organization = cls.create(name=name)
            txn.commit()
        return organization

    def dump(self, with_users: bool = True) -> dict:
        data = {
            'id': str(self.id),
            'name': self.name,
        }

        if with_users and self.users:
            users = [u.dump(with_organization=False)
                     for u in self.users]
            users.sort(key=lambda u: u['name'])
            data['users'] = users
        return data
