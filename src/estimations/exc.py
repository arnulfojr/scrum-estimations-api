
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
