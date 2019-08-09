"""Users models module.

Contains the models of all the users regarding the admin tool.
"""
from datetime import datetime
from uuid import uuid4

from tortoise.models import Model, fields

from common.loggers import logger
from organizations.models import Organization


DEFAULT_NAME = 'User'

ROLES = (
    'USER',
    'ADMIN',
    'SUPER_ADMIN',
)


class User(Model):
    """User from the admin tool.

    This model relates to an organization.
    """
    id = fields.IntField(pk=True)

    email = fields.CharField(max_length=255, null=False, unique=True)

    name = fields.CharField(max_length=255, default=DEFAULT_NAME)

    password = fields.CharField(max_length=255, null=False)

    role = fields.CharField(max_length=255, default=ROLES[0])

    # TODO: support toroise in organizations
    organization = fields.ForeignKeyField(Organization, related_name='users',
                                          db_column='organization',
                                          null=True, default=None)

    registered_on = fields.DatetimeField(auto_now_add=True)

    class Meta:

        table = 'users'

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
