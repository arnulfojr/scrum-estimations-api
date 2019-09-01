"""Users models module.

Contains the models of all the users regarding the admin tool.
"""
from datetime import datetime
from typing import Optional, Union
from uuid import UUID, uuid4

import peewee

from common.db import database
from organizations.models import Organization

from .exceptions import NotFound, UserAlreadyExists


DEFAULT_NAME = 'User'

ROLES = (
    'USER',
    'ADMIN',
    'SUPER_ADMIN',
)


class User(peewee.Model):
    """User from the admin tool.

    This model relates to an organization.
    """
    id = peewee.UUIDField(primary_key=True, default=uuid4)

    email = peewee.CharField(null=False, unique=True)

    name = peewee.CharField(default=DEFAULT_NAME)

    password = peewee.CharField(null=True, default=None)

    role = peewee.CharField(default=ROLES[0])

    organization = peewee.ForeignKeyField(Organization, backref='users',
                                          column_name='organization_id',
                                          null=True, default=None)

    registered_on = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        table_name = 'users'

    @classmethod
    def lookup(cls, identifier) -> Optional['User']:
        user_query = cls.select().where(cls.id == identifier)
        try:
            user = user_query.get()
        except cls.DoesNotExist as e:
            raise NotFound(f'User with ID {identifier} was not found', e) from e
        else:
            return user

    @classmethod
    def get_by_email(cls, email: str) -> 'User':
        user_query = cls.select().where(cls.email == email)
        try:
            user = user_query.get()
        except cls.DoesNotExist as e:
            raise NotFound(f'User with email {email} was not found', e) from e
        else:
            return user

    @classmethod
    def create_from(cls, data: dict) -> 'User':
        email = data['email']
        name = data.get('name')
        password = data.get('password')
        role = data.get('role', ROLES[0])
        organization = data.get('organization')

        try:
            with database.atomic() as txn:
                user = cls.create(email=email, name=name, password=password,
                                  role=role, organization=organization)
                txn.commit()
        except peewee.IntegrityError as e:
            raise UserAlreadyExists(f'User with {email} is already registered', e) from e
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

    def belongs_to_organization(self, organization: Union[Organization, UUID, str]) -> bool:
        if not self.organization:
            return False

        if isinstance(organization, Organization):
            return self.organization == organization

        if isinstance(organization, UUID):
            organization = str(organization)

        return str(self.organization.id) == organization

    def dump(self, with_organization: bool = False):
        """Dump the object to a primitive dictionary."""
        user = {
            'id': str(self.id),
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'registered_on': self.registered_on.isoformat(),
        }

        if with_organization:
            if self.organization:
                user['organization'] = self.organization.dump(with_users=False)
            else:
                user['organization'] = None

        return user
