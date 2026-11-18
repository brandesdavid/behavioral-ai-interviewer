"""Errors that map to an HTTP response without a stack trace."""


class ClientError(Exception):
    """The request itself is invalid. `status` is the HTTP status to return."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status
