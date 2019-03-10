from datetime import datetime
from uuid import uuid4

import peewee

from common.db import database
from common.db import MixinModel
from organizations.models import Organization
from users.models import User


class Session(MixinModel, peewee.Model):
    """Estimations Session."""

    created_at = peewee.TimestampField(default=datetime.now)

    name = peewee.CharField()

    organization = peewee.ForeignKeyField(Organization, related_name='sessions')

    completed = peewee.BooleanField()

    completed_at = peewee.TimestampField(null=True)

    class Meta:

        database = database

        db_table = 'sessions'


class SessionMember(MixinModel, peewee.Model):
    """The session members."""

    session = peewee.ForeignKeyField(Session, related_name='session_members')

    user = peewee.ForeignKeyField(User, related_name='session_members')

    class Meta:

        database = database

        db_table = 'session_members'


class Task(MixinModel, peewee.Model):
    """Task model."""

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    name = peewee.CharField()

    created_at = peewee.TimestampField(default=datetime.now)

    session = peewee.ForeignKeyField(Session, related_name='tasks')

    class Meta:

        database = database

        db_table = 'tasks'


class Sequence(MixinModel, peewee.Model):
    """Sequence model."""

    class Meta:

        database = database

        db_table = 'sequences'


class EstimationStep(MixinModel, peewee.Model):
    """Estimation step."""

    class Meta:

        database = database

        db_table = 'estimation_steps'

