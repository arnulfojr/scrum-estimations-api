class UserException(Exception):
    """User base exception."""


class NotFound(UserException):
    """Exception when a user is not found."""
