from typing import Any

from tiddl.common.exceptions import AppException


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
