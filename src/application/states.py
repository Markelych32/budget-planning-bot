from typing import Any, Callable

from src.infrastructure.errors import DeprecatedMessage
from src.infrastructure.models import FlexModel


class State:
    _instances: dict[int, "State"] = {}

    def __new__(cls, user_id: int) -> "State":
        if existed_state := cls._instances.get(user_id):
            return existed_state

        cls._instances[user_id] = super().__new__(cls)

        return cls._instances[user_id]

    def __init__(self, user_id: int):
        if getattr(self, "__initialized", False):
            return

        self.next_callback: Callable | None = None
        self.data: FlexModel = FlexModel()
        self.messages_to_delete: set[int] = set()

        setattr(self, "__initialized", True)

    def populate_data(self, payload: dict[str, Any]):
        for field, value in payload.items():
            setattr(self.data, field, value)

    def clear_data(self):
        for key in self.data.dict().keys():
            delattr(self.data, key)

    def check_data(self, *fields: str) -> None:
        existed_fields = set(self.data.dict().keys())
        if set(fields) - existed_fields:
            raise DeprecatedMessage
