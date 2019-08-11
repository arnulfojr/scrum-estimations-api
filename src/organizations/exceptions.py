class OrganizationException(Exception):
    """Base organization exception."""


class NotFound(OrganizationException):
    """Organization was not found."""
