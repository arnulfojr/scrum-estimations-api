"""Estimations models.

Here is a short story of the models:

    A Scrum estimation session happens in an organization.
    Each estimation session has some team members that participate.
    In every session a limited set of tasks are estimated by the members.
    The members use a sequence to closely describe the task complexity.
        Sequences are chained/linked values,
        each having a numeric value and a name (e.g., shirt-size).
        The numeric value is used to calculate the average of the estimated task,
        and to match the closest estimation.
        The name (optionally) can be used to abstract away the numeric value.
"""
from datetime import datetime
from uuid import uuid4

import peewee

from common.db import database, manager
from common.db import MixinModel
from organizations.models import Organization
from users.models import User

from .exc import ResourceAlreadyExists


class Sequence(MixinModel, peewee.Model):
    """Sequence model."""

    name = peewee.CharField(primary_key=True)

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        db_table = 'sequences'

    @classmethod
    async def get(cls, name: str):
        """Return the sequence by name."""
        try:
            sequence = await manager.get(cls, name=name)
        except cls.DoesNotExist:
            return None
        else:
            return sequence

    @classmethod
    async def all(cls):
        """Return all instances."""
        query = cls.select()

        results = await manager.execute(query)

        sequences = [seq for seq in results]
        return sequences

    @classmethod
    async def from_data(cls, *, name: str):
        try:
            instance = await manager.create(cls, name=name)
        except peewee.IntegrityError as e:
            raise ResourceAlreadyExists(f'Sequence with name {name} already exists') from e

        return instance

    def dump(self) -> dict:
        return {
            'name': self.name,
            'created_at': self.created_at.isoformat(),
        }


class Value(MixinModel, peewee.Model):
    """Estimation value."""

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    sequence = peewee.ForeignKeyField(Sequence, related_name='estimation_values')

    previous = peewee.ForeignKeyField('self', null=True, related_name='next_value')

    next = peewee.ForeignKeyField('self', null=True, related_name='previous_value')

    name = peewee.CharField(null=True)

    value = peewee.IntegerField(null=True)

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        indexes = (
            (('previous_step', 'next_step'), True),
        )

        database = database

        db_table = 'estimation_values'

    @classmethod
    async def get_from_sequence(cls, sequence: Sequence):
        prev_values = cls.select().alias()
        next_values = cls.select().alias()
        query = cls.select()
        query = query.join(prev_values, on=(cls.previous == cls.id))
        query = query.join(next_values, on=(cls.next == cls.id))
        query = query.join(Sequence, on=(cls.sequence.name == Sequence.name))
        query = query.where(cls.sequence.name == sequence.name)

        from pudb.remote import set_trace
        set_trace(term_size=(120, 64))

        results = await manager.execute(query)
        return [value for value in results]

    async def from_data(cls, *, sequence: Sequence, previous, next, name: str, value: int):
        pass


class Session(MixinModel, peewee.Model):
    """Estimations Session."""

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    name = peewee.CharField()

    organization = peewee.ForeignKeyField(Organization, related_name='sessions')

    sequence = peewee.ForeignKeyField(Sequence, related_name='sessions')

    completed = peewee.BooleanField(default=False)

    completed_at = peewee.TimestampField(null=True)

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        db_table = 'sessions'


class SessionMember(MixinModel, peewee.Model):
    """The session members."""

    session = peewee.ForeignKeyField(Session, related_name='session_members')

    user = peewee.ForeignKeyField(User, related_name='session_members')

    class Meta:

        primary_key = False

        indexes = (
            (('session', 'user'), True),
        )

        database = database

        db_table = 'session_members'


class Task(MixinModel, peewee.Model):
    """Task model."""

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    name = peewee.CharField(index=True)

    session = peewee.ForeignKeyField(Session, related_name='tasks')

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        db_table = 'tasks'


class Estimation(MixinModel, peewee.Model):
    """Estimation of a user."""

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    task = peewee.ForeignKeyField(Task, related_name='estimations')

    user = peewee.ForeignKeyField(User, related_name='estimations')

    value = peewee.ForeignKeyField(Value, related_name='estimations')

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        indexes = (
            (('task', 'user'), False),
        )

        database = database

        db_table = 'estimations'


class EstimationSummary(MixinModel, peewee.Model):
    """Estimation summary."""

    task = peewee.ForeignKeyField(Task, related_name='summaries')

    closet_value = peewee.ForeignKeyField(Value)

    average = peewee.DecimalField()

    concensus_met = peewee.BooleanField()

    class Meta:

        database = database

        db_table = 'estimation_summaries'
