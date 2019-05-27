"""Users models module.

Contains the models of all the users regarding the admin tool.
"""
from datetime import datetime
from uuid import uuid4

import peewee

from common.db import database
from common.db import manager
from common.db import MixinModel
from common.loggers import logger
from organizations.models import Organization


DEFAULT_NAME = 'User'

ROLES = (
    'USER',
    'ADMIN',
    'SUPER_ADMIN',
)


class User(MixinModel, peewee.Model):
    """User from the admin tool.

    This model relates to an organization.
    """
    id = peewee.UUIDField(primary_key=True, default=uuid4)

    email = peewee.CharField(null=False, unique=True)

    name = peewee.CharField(default=DEFAULT_NAME)

    password = peewee.CharField()

    role = peewee.CharField(default=ROLES[0])

    organization = peewee.ForeignKeyField(Organization, related_name='users',
                                          db_column='organization',
                                          null=True, default=None)

    registered_on = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        db_table = 'users'

    @classmethod
    async def get(cls, id):
        user_query = cls.select().where(cls.id == id)
        matches = await manager.prefetch(user_query,
                                         Organization.select())
        matches = list(matches)
        if not matches:
            return None
        return matches[0]

    @classmethod
    async def create_from(cls, data: dict):
        email = data['email']
        name = data.get('name')
        password = data.get('password')
        role = data.get('role', ROLES[0])
        organization = data.get('organization')

        try:
            user = await manager.create(cls, email=email,
                                        name=name,
                                        password=password,
                                        role=role,
                                        organization=organization)
        except peewee.InternalError as e:
            logger.error(str(e))
            return None
        else:
            return user

    def update_from(self, *, email: str = '', name: str = '',
                    password: str = '', role: str = '', **kwargs):
        """Update user from the given data."""
        self.email = email or self.email
        self.name = name or self.name
        self.password = password or self.password
        self.role = role or self.role

        return self

    def dict_dump(self, with_organization: bool = False):
        """Dump the object to a primitive dictionary."""
        user = {
            'id': str(self.id),
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'registered_on': self.registered_on.isoformat(),
        }

        if with_organization:
            user['organization'] = self.organization.dict_dump() if self.organization else None

        return user
