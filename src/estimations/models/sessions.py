import statistics

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union
from uuid import UUID, uuid4

import peewee

from common.db import database
from common.loggers import logger
from organizations.models import Organization
from users.models import User

from .sequences import Sequence, Value
from ..exc import (
    SessionNotFound,
    TaskNotFound,
    UserIsNotPartOfTheSession,
)


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
            members: List[User] = [member.user.dump() for member in self.session_members]
            members.sort(key=lambda member: member.get('registered_on'))
            data['members'] = members

        if with_tasks and self.tasks:
            tasks = [task.dump(with_session=False) for task in self.tasks]
            tasks.sort(key=lambda task: task.get('name', ''))
            data['tasks'] = tasks

        return data


class SessionMember(peewee.Model):
    """The session members."""

    session = peewee.ForeignKeyField(Session, backref='session_members',
                                     on_delete='CASCADE',
                                     column_name='session')

    user = peewee.ForeignKeyField(User, backref='session_user',
                                  on_delete='CASCADE',
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
            estimations: List[dict] = [estimation.dump(with_task=False)
                                       for estimation in self.estimations]
            estimations.sort(key=lambda estimation: estimation.get('created_at'))
            data['estimations'] = estimations

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
    def lookup(cls, task: Task, user: User) -> Optional['Estimation']:
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
