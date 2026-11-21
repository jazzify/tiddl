from typing import Any


# Base Exception
class AppException(Exception):
    def __init__(self, key: str, message: str, extra: dict[str, Any] | None = None):
        super().__init__(f"{key}: {message}")
        self.key = key
        self.message = message
        self.extra = extra

    def __str__(self):
        return f"{self.key}: {self.message} {self.extra}"


# CLI Exceptions
class CLIBaseException(AppException):
    def __init__(
        self,
        key: str = "CLI_BASE_EXCEPTION",
        message: str = "",
        extra: dict[str, Any] | None = None,
    ):
        super().__init__(key, message, extra)
        self.key = key
        self.message = message


class CLIValidationException(CLIBaseException):
    def __init__(
        self,
        key: str = "CLI_VALIDATION_EXCEPTION",
        message: str = "",
        extra: dict[str, Any] | None = None,
    ):
        super().__init__(key, message, extra)
        self.key = key
        self.message = message


# API Exceptions
class ApiError(Exception):
    def __init__(self, status: int, subStatus: str, userMessage: str):
        self.status = status
        self.sub_status = subStatus
        self.user_message = userMessage

    def __str__(self):
        return f"{self.user_message}, {self.status}/{self.sub_status}"


# Auth Exceptions
class AuthClientError(Exception):
    def __init__(
        self,
        status: int | None = None,
        error: str | None = None,
        sub_status: str | None = None,
        error_description: str | None = None,
    ):
        self.status = status
        self.error = error
        self.sub_status = sub_status
        self.error_description = error_description

    def __str__(self):
        return (
            f"{self.error}, {self.error_description}, {self.status}/{self.sub_status}"
        )
