"""Lightweight logging wrapper used by the ingestion subsystem."""
from __future__ import annotations

import logging
from typing import Any


class Logger:
    """Simple proxy around :mod:`logging` providing a stable interface."""

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.exception(message, *args, **kwargs)

    def setLevel(self, level: int) -> None:  # noqa: N802 - keep logging API style
        self._logger.setLevel(level)


__all__ = ["Logger"]
