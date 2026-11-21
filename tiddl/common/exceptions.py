from typing import Any


class AppException(Exception):
    def __init__(self, key: str, message: str, extra: dict[str, Any] | None = None):
        super().__init__(f"{key}: {message}")
        self.key = key
        self.message = message
        self.extra = extra

    def __str__(self):
        return f"{self.key}: {self.message} {self.extra}"
