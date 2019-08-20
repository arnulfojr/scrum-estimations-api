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
import statistics

from datetime import datetime
from decimal import Decimal
from itertools import chain, islice, tee
from typing import Any, Iterator, List, Union
from uuid import UUID, uuid4

import peewee

from common.db import database
from common.loggers import logger
from organizations.models import Organization
from users.models import User

from .exc import ResourceAlreadyExists, SequenceNotFound, SessionNotFound
from .exc import TaskNotFound, UserIsNotPartOfTheSession, ValueNotFound


class Sequence(peewee.Model):
    """Sequence model.

    Receives the backref from:
        * Value as values
    """

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
    def sorted_values(self) -> List['Value']:
        """Returns a sorted list of the values."""
        if not self.values:
            logger.error('No values found')
            return list()

        numeric_values = [val for val in self.values if val.value is not None]
        if not numeric_values:
            logger.error('Did not found any numeric values')
            return self.values

        root_generator = (nv for nv in numeric_values
                          if nv.previous is None and nv.next is not None)
        root_value = next(root_generator, None)
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

        non_numeric_values = [val for val in self.values if val.value is None]
        if non_numeric_values:
            # sort in place by name, fallback to value's ID
            non_numeric_values.sort(key=lambda v: v.name or str(v.id))

        values.extend(non_numeric_values)
        return values

    def value_pairs(self, only_numeric=True):
        """Yields the current value and the next value as a 2-value tuple.

        The first pair is (index0, index1) and last pair is (indexN, None).
        Example usage:

        for value, next_value in self.value_pairs():
            pass
        """
        # TODO: add unit test here
        values = self.values
        if only_numeric:
            values = [value for value in self.values if value.value is not None]

        if not values:
            return
        value = values[0]
        while value:
            yield value, value.next
            value = value.next

    def closest_possible_value(self, value: Union[Decimal, float],  # noqa: C901
                               round_up=True) -> Union['Value', None]:
        """Returns the closest possible value in the sequence's values based on the given value."""
        # TODO: add unit test here
        if isinstance(value, float):
            value = Decimal(value)

        left, right = None, None
        for val, next_val in self.value_pairs(only_numeric=True):
            if next_val is None:
                left, right = None, val
                break  # there should not be anymore items
            if val.value <= value <= next_val.value:
                left, right = val, next_val

        if left is None and right is None:
            return None
        if left is not None and right is None:
            return left
        if left is None and right is not None:
            return right

        diff_left = abs(left.value - value)
        diff_right = abs(right.value - value)
        if diff_left == diff_right:
            return left if not round_up else right
        if diff_left < diff_right:
            return left
        return right

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

    sequence = peewee.ForeignKeyField(Sequence, field='name', backref='values',
                                      on_delete='CASCADE',
                                      column_name='sequence')

    previous = peewee.ForeignKeyField('self', null=True, backref='next_value',
                                      on_delete='SET NULL',
                                      column_name='previous')

    next = peewee.ForeignKeyField('self', null=True, backref='previous_value',
                                  on_delete='SET NULL',
                                  column_name='next')

    name = peewee.CharField(null=True)

    value: Decimal = peewee.DecimalField(null=True)

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        indexes = (
            (('previous', 'next'), True),
        )

        database = database

        table_name = 'estimation_values'

    @classmethod
    def lookup(cls, identifier: str):
        query = cls.select().where(cls.id == identifier)
        try:
            value = query.get()
        except cls.DoesNotExist as e:
            raise ValueNotFound(f'No value for {identifier} was found') from e
        else:
            return value

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

                value = cls(name=item.get('name'),
                            sequence=sequence,
                            value=normalized_value)
                value.save(force_insert=True)
                values.append(value)

        numeric_values = [v for v in values if v.value is not None]
        numeric_values.sort(key=lambda v: v.value)

        non_numeric_values = [v for v in values if v.value is None]
        non_numeric_values.sort(key=lambda v: v.name)

        for previous, current, nxt in previous_and_next(numeric_values):
            current.previous = previous
            current.next = nxt

        with database.atomic():
            for value in numeric_values:
                value.save()

        sorted_values = list()
        sorted_values.extend(numeric_values)
        sorted_values.extend(non_numeric_values)

        return sorted_values

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
    """Estimations Session.

    Receives the backref from:
        * SessionMember as session_members
        * Task as tasks
    """

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    name = peewee.CharField()

    organization = peewee.ForeignKeyField(Organization, backref='sessions',
                                          on_delete='CASCADE')

    sequence = peewee.ForeignKeyField(Sequence, backref='sessions',
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

    def dump(self, with_organization=True, with_tasks=True):
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

        if with_tasks and self.tasks:
            data['tasks'] = [task.dump(with_session=False) for task in self.tasks]

        return data


class SessionMember(peewee.Model):
    """The session members."""

    session = peewee.ForeignKeyField(Session, backref='session_members',
                                     column_name='session')

    user = peewee.ForeignKeyField(User, backref='session_user',
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
    """Task model.

    Receives the backref:
        * Estimation as estimations
        * EstimationSummary as summaries
    """

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    name = peewee.CharField(index=True)

    session = peewee.ForeignKeyField(Session, backref='tasks',
                                     on_delete='CASCADE',
                                     column_name='session')

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        table_name = 'tasks'

    @classmethod
    def lookup(cls, name_or_id: Union[UUID, str], session: Union[Session, None] = None):
        if isinstance(name_or_id, UUID):  # then for sure it is the Task ID
            query = cls.select().where(cls.id == name_or_id)
        else:
            # well it could be either the Task ID or the name...
            try:
                name_or_id = UUID(name_or_id)
            except (ValueError, TypeError):  # for sure then it is the name
                if not session:
                    # we kind of need the session for it
                    logger.error(f'While trying to lookup the Task {name_or_id} we got no session')
                    raise
                query = cls.select().where(
                    (cls.name == name_or_id) & (cls.session == session))
            else:
                # we know we are referring to the Task ID
                query = cls.select().where(cls.id == name_or_id)

        if query is None:
            raise TaskNotFound('No query for Task search could be built')

        try:
            task = query.get()
        except cls.DoesNotExist as e:
            raise TaskNotFound('Task was not found') from e
        else:
            return task

    @property
    def is_estimated_by_all_members(self) -> bool:
        """Returns a boolean if everybody has estimated the task."""
        users_who_estimated: List[User] = [estimation.user for estimation in self.estimations]
        session_users: List[User] = [member.user for member in self.session.session_members]

        return all((user in users_who_estimated) for user in session_users)

    @property
    def consensus_met(self) -> bool:
        """Returns True if all the estimations are the same."""
        values: List[Value] = [estimation.value for estimation in self.estimations]
        try:
            first_value: Value = values.pop()
        except IndexError:
            return False
        return all((value == first_value) for value in values)

    @property
    def mean_estimation(self) -> Decimal:
        """Return the mean for the numeric estimated values.

        Returns a Decimal(0) if casting the mean failed.
        """
        values = (estimation.value for estimation in self.estimations)
        numeric_values = (value.value for value in values
                          if value.value is not None)
        try:
            average: Decimal = statistics.mean(numeric_values)
        except (statistics.StatisticsError, TypeError):
            return Decimal(0)
        else:
            return average

    def has_non_numeric_estimations(self) -> bool:
        """Returns True if an estimation has no numerical value."""
        values = (estimation.value for estimation in self.estimations)
        return any(value for value in values if value.value is None)

    @property
    def non_numeric_estimations(self) -> List['Estimation']:
        """Returns the estimations that have no numerical value."""
        return [estimation for estimation in self.estimations if estimation.value.value is None]

    def dump(self, with_session=True, with_organization=False, with_estimations=False) -> dict:
        data = {
            'id': str(self.id),
            'name': self.name,
            'created_at': self.created_at.isoformat(),
        }

        if with_session:
            data['session'] = self.session.dump(with_tasks=True,
                                                with_organization=with_organization)

        if with_estimations:
            data['estimations'] = [estimation.dump(with_task=False)
                                   for estimation in self.estimations]

        return data


class Estimation(peewee.Model):
    """Estimation of a user."""

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    task = peewee.ForeignKeyField(Task, backref='estimations',
                                  column_name='task',
                                  on_delete='CASCADE')

    user = peewee.ForeignKeyField(User, backref='estimations',
                                  column_name='user',
                                  on_delete='SET NULL')

    value = peewee.ForeignKeyField(Value, backref='estimations',
                                   column_name='value',
                                   on_delete='SET NULL')

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        table_name = 'estimations'

    @classmethod
    def lookup(cls, task: Task, user: User) -> 'Estimation':
        query = cls.select().where((cls.task == task) & (cls.user == user))
        try:
            estimation = query.get()
        except cls.DoesNotExist:
            return None
        else:
            return estimation

    def dump(self, with_task=True):
        data = {
            'user': self.user.dump(with_organization=False),
            'value': self.value.dump(),
            'created_at': self.created_at.isoformat(),
        }

        if with_task:
            data['task'] = self.task.dump(with_session=False)

        return data


class EstimationSummary(peewee.Model):
    """Estimation summary."""

    task = peewee.ForeignKeyField(Task, backref='summaries')

    closet_value = peewee.ForeignKeyField(Value)

    average = peewee.DecimalField()

    consensus_met = peewee.BooleanField()

    class Meta:

        database = database

        table_name = 'estimation_summaries'
