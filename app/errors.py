"""
Utility to handle exceptions
"""

class CustomError(Exception):
    """
    Base class for custom application errors.
    """
    status_code: int = 500
    error_code: str = "UNEXPECTED_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, status_code: int | None = None, error_code: str | None = None):
        super().__init__(message or self.message)
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code


class NotFoundError(CustomError):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "The requested item could not be found."

    def __init__(self, name: str):
        super().__init__(message=f"Oops! No {name} were found.")

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
