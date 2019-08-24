from http import HTTPStatus
from typing import Union


def add_status_code(code: HTTPStatus):
    def class_decorator(cls):
        cls.status_code = code
        return cls

    return class_decorator


class EstimationsException(Exception):
    """Base exception."""

    def __init__(self, message: str, status_code: Union[HTTPStatus, None] = None):
        super().__init__(message)

        if status_code is not None:
            self.status_code = status_code


@add_status_code(HTTPStatus.BAD_REQUEST)
class InvalidRequest(EstimationsException):
    """Invalid request."""


@add_status_code(HTTPStatus.BAD_REQUEST)
class EmptyIdentifier(InvalidRequest):
    """Empty identifier."""


@add_status_code(HTTPStatus.UNPROCESSABLE_ENTITY)
class ResourceAlreadyExists(EstimationsException):
    """Resource Already exists."""


@add_status_code(HTTPStatus.NOT_FOUND)
class ResourceNotFound(EstimationsException):
    """Resource does not exist."""


@add_status_code(HTTPStatus.NOT_FOUND)
class SequenceNotFound(ResourceNotFound):
    """The Sequence was not found."""


@add_status_code(HTTPStatus.NOT_FOUND)
class SessionNotFound(ResourceNotFound):
    """The session was not found."""


@add_status_code(HTTPStatus.NOT_FOUND)
class UserIsNotPartOfTheSession(ResourceNotFound):
    """The member is not part of the session."""


@add_status_code(HTTPStatus.NOT_FOUND)
class TaskNotFound(ResourceNotFound):
    """The task was not found."""


@add_status_code(HTTPStatus.NOT_FOUND)
class ValueNotFound(ResourceNotFound):
    """The value was not found."""
