from enum import StrEnum, auto
from typing import Any

__all__ = ("MessageType", "DEFAULT_SEND_SETTINGS")

DEFAULT_SEND_SETTINGS: dict[str, Any] = {"parse_mode": "HTML"}


class MessageType(StrEnum):
    REGULAR = auto()
    CALLBACK = auto()
