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
from .sequences import (
    Sequence,
    Value,
)
from .sessions import (
    Estimation,
    Session,
    SessionMember,
    Task,
)


__all__ = [
    'Estimation',
    'Sequence',
    'Session',
    'SessionMember',
    'Task',
    'Value',
]
