from http import HTTPStatus


def add_status_code(code: HTTPStatus):
    def class_decorator(cls):
        cls.status_code = code
        return cls

    return class_decorator


class UserException(Exception):
    """User base exception."""

    def __str__(self):
        if self.args:
            message = self.args[0]
        elif hasattr(self, 'message'):
            message = self.message
        else:
            message = 'User Exception'

        return message


@add_status_code(HTTPStatus.NOT_FOUND)
class NotFound(UserException):
    """Exception when a user is not found."""


@add_status_code(HTTPStatus.UNPROCESSABLE_ENTITY)
class UserAlreadyExists(UserException):
    """Exception raised when attempting to create an already registered user."""
