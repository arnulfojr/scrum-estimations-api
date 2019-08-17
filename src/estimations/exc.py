
class EstimationsException(Exception):
    """Base exception."""


class ResourceAlreadyExists(EstimationsException):
    """Resource Already exists."""


class ResourceNotFound(EstimationsException):
    """Resource does not exist."""


class SequenceNotFound(ResourceNotFound):
    """The Sequence was not found."""


class SessionNotFound(ResourceNotFound):
    """The session was not found."""


class UserIsNotPartOfTheSession(ResourceNotFound):
    """The member is not part of the session."""
