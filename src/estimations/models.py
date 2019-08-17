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
from decimal import Decimal
from itertools import chain, islice, tee
from typing import Any, Iterator, List
from uuid import uuid4

import peewee

from common.db import database
from common.loggers import logger
from organizations.models import Organization
from users.models import User

from .exc import ResourceAlreadyExists, SequenceNotFound, SessionNotFound, UserIsNotPartOfTheSession


class Sequence(peewee.Model):
    """Sequence model."""

    name = peewee.CharField(primary_key=True)

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        table_name = 'sequences'

    @classmethod
    def lookup(cls, name: str) -> 'Sequence':
        """Return the sequence by name."""
        query = cls.select().where(cls.name == name)
        try:
            sequence = query.get()
        except cls.DoesNotExist as e:
            raise SequenceNotFound(f'Sequence with name {name} was not found') from e
        else:
            return sequence

    @classmethod
    def all(cls) -> List['Sequence']:
        """Return all instances."""
        query = cls.select()
        return list(query)

    @classmethod
    def from_data(cls, *, name: str) -> 'Sequence':
        try:
            instance = cls.create(name=name)
        except peewee.IntegrityError as e:
            raise ResourceAlreadyExists(f'Sequence with name {name} already exists') from e
        else:
            return instance

    def dump(self, with_values=True) -> dict:
        data = {
            'name': self.name,
            'created_at': self.created_at.isoformat(),
        }

        if with_values:
            data['values'] = [value.dump() for value in self.sorted_values]

        return data

    @property
    def sorted_values(self):
        if not self.values:
            logger.error('No values found')
            return list()

        numeric_values = list(filter(lambda v: v.value is not None, self.values))
        if not numeric_values:
            logger.error('Did not found any numeric values')
            return self.values

        root_value = next((nv for nv in numeric_values
                           if nv.previous is None and nv.next is not None), None)
        if root_value is None:
            logger.error(f'No root value, can not sort in {numeric_values}')
            return self.values

        value, values = root_value, list()
        values.append(value)
        while value.next:
            value = value.next
            if value:
                values.append(value)
            else:
                break

        non_numeric_values = list(filter(lambda v: v.value is None, self.values))
        if non_numeric_values:
            # sort in place by name, fallback to value's ID
            non_numeric_values.sort(key=lambda v: v.name or str(v.id))

        values.extend(non_numeric_values)
        return values

    def remove_values(self):
        """Removes the related values in an atomic way."""
        values = self.sorted_values
        if not values:
            return
        with database.atomic():
            for value in values:
                value.delete_instance()


class Value(peewee.Model):
    """Estimation value."""

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    sequence = peewee.ForeignKeyField(Sequence, field='name', related_name='values',
                                      on_delete='CASCADE',
                                      column_name='sequence')

    previous = peewee.ForeignKeyField('self', null=True, related_name='next_value',
                                      on_delete='SET NULL',
                                      column_name='previous')

    next = peewee.ForeignKeyField('self', null=True, related_name='previous_value',
                                  on_delete='SET NULL',
                                  column_name='next')

    name = peewee.CharField(null=True)

    value = peewee.DecimalField(null=True)

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        indexes = (
            (('previous', 'next'), True),
        )

        database = database

        table_name = 'estimation_values'

    @classmethod
    def from_list(cls, items: List[dict], sequence: Sequence) -> List['Value']:
        values = list()

        with database.atomic():
            for item in items:
                val = item.get('value')
                try:
                    normalized_value = Decimal(val)
                except TypeError:
                    logger.error(f'Value({val}) was not Decimal and will use None')
                    normalized_value = None

                value = cls.create(name=item.get('name'),
                                   sequence=sequence,
                                   value=normalized_value)
                values.append(value)

        numeric_values = list(filter(lambda x: x.value is not None, values))
        for previous, current, nxt in previous_and_next(numeric_values):
            current.previous = previous
            current.next = nxt

        with database.atomic():
            for value in numeric_values:
                value.save()

        return values

    def dump(self):
        payload = {
            'id': self.id,
        }

        if self.name:
            payload['name'] = self.name

        if self.value is not None:
            payload['value'] = float(self.value)
        else:
            payload['value'] = None

        return payload


def previous_and_next(some_iterable: Iterator[Any]):
    """Iterate over a 3-tuple valued as (previous, current, next)."""
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)


class Session(peewee.Model):
    """Estimations Session."""

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    name = peewee.CharField()

    organization = peewee.ForeignKeyField(Organization, related_name='sessions',
                                          on_delete='CASCADE')

    sequence = peewee.ForeignKeyField(Sequence, related_name='sessions',
                                      column_name='sequence')

    completed = peewee.BooleanField(default=False)

    completed_at = peewee.TimestampField(null=True)

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        table_name = 'sessions'

    @classmethod
    def lookup(cls, code: str):
        query = cls.select().where(cls.id == code)
        try:
            session = query.get()
        except cls.DoesNotExist as e:
            raise SessionNotFound(f'Session with name {code} was not found') from e
        else:
            return session

    @classmethod
    def from_data(cls, name, organization: dict, sequence: dict) -> 'Session':
        try:
            organization_id = organization['id']
            sequence_name = sequence['name']
        except KeyError as e:
            logger.error(f'Expected the organization to have an ID or '
                         f'the Sequence to have a name - {e}')
            raise

        sequence_model = Sequence.lookup(sequence_name)
        organization_model = Organization.lookup(organization_id)
        session = cls.create(name=name,
                             organization=organization_model,
                             sequence=sequence_model)
        return session

    def dump(self, with_organization=True):
        data = {
            'id': str(self.id),
            'name': self.name,
            'completed': self.completed,
            'created_at': self.completed_at.isoformat(),
        }

        if self.completed and self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()

        data['sequence'] = self.sequence.dump()

        if with_organization:
            data['organization'] = self.organization.dump()

        if self.session_members:
            data['members'] = [member.user.dump() for member in self.session_members]

        return data


class SessionMember(peewee.Model):
    """The session members."""

    session = peewee.ForeignKeyField(Session, related_name='session_members',
                                     column_name='session')

    user = peewee.ForeignKeyField(User, related_name='session_user',
                                  column_name='user')

    class Meta:

        primary_key = False

        indexes = (
            (('session', 'user'), True),
        )

        database = database

        table_name = 'session_members'

    @classmethod
    def lookup(cls, session: Session, user: User) -> 'SessionMember':
        query = cls.select().where((cls.session == session) & (cls.user == user))

        try:
            member = query.get()
        except cls.DoesNotExist as e:
            raise UserIsNotPartOfTheSession(f'User({user.id}) has not join '
                                            f'the Session({session.id})') from e
        else:
            return member

    def leave(self):
        query = SessionMember.delete().where(
            (SessionMember.session == self.session) & (SessionMember.user == self.user))

        return query.execute()

    def dump(self, with_user=True):
        data = {
            'session': self.session.dump(),
        }

        if with_user:
            data['user'] = self.user.dump(with_organization=False)

        return data


class Task(peewee.Model):
    """Task model."""

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    name = peewee.CharField(index=True)

    session = peewee.ForeignKeyField(Session, related_name='tasks')

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        table_name = 'tasks'


class Estimation(peewee.Model):
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

        table_name = 'estimations'


class EstimationSummary(peewee.Model):
    """Estimation summary."""

    task = peewee.ForeignKeyField(Task, related_name='summaries')

    closet_value = peewee.ForeignKeyField(Value)

    average = peewee.DecimalField()

    consensus_met = peewee.BooleanField()

    class Meta:

        database = database

        table_name = 'estimation_summaries'
