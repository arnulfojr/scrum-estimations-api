class UserException(Exception):
    """User base exception."""

    def __str__(self):
        if len(self.args) > 0:
            message = self.args[0]
        elif hasattr(self, 'message'):
            message = self.message
        else:
            message = 'User Exception'

        return message


class NotFound(UserException):
    """Exception when a user is not found."""


class UserAlreadyExists(UserException):
    """Exception raised when attempting to create an already registered user."""
