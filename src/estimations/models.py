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

from common.db import database
from common.db import MixinModel
from organizations.models import Organization
from users.models import User


class Sequence(MixinModel, peewee.Model):
    """Sequence model."""

    name = peewee.CharField(primary_key=True)

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        db_table = 'sequences'


class Value(MixinModel, peewee.Model):
    """Estimation step."""

    sequence = peewee.ForeignKeyField(Sequence, related_name='estimation_steps')

    previous_step = peewee.ForeignKeyField('self', null=True)

    next_step = peewee.ForeignKeyField('self', null=True)

    name = peewee.CharField(null=True)

    value = peewee.IntegerField(null=True)

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        indexes = (
            (('previous_step', 'next_step'), True),
        )

        database = database

        db_table = 'estimation_steps'


class Session(MixinModel, peewee.Model):
    """Estimations Session."""

    created_at = peewee.TimestampField(default=datetime.now)

    name = peewee.CharField()

    organization = peewee.ForeignKeyField(Organization, related_name='sessions')

    sequence = peewee.ForeignKeyField(Sequence, related_name='sessions')

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
