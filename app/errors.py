"""
Utility to handle exceptions
"""


class NotFoundError(Exception):
    """
    An item can not be found
    """

    def __init__(self, name: str):
        self.name = name


class InconsistentDatabaseError(Exception):
    """
    An inconsistent value was detected on the database
    """

    def __init__(self, name: str, details: str | None = None):
        self.name = name
        self.details = details


class BadRequestError(Exception):
    """
    The request is made inconsistent
    """

    def __init__(self, details: str):
        self.details = details


class ForbiddenError(Exception):
    """
    The request is made inconsistent
    """

    def __init__(self, details: str = "Forbidden"):
        self.details = details


class UnauthorizedError(Exception):
    """
    The verification could not be verified
    """

    def __init__(self, name: str):
        self.name = name


class NoRecordedVotes(Exception):
    """
    We can't display results if we don't have resutls
    """
