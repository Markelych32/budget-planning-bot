from uuid import uuid4

from pydantic import Field

from src.infrastructure.models import InternalModel


class CallbackItem(InternalModel):

    name: str
    callback_data: str = Field(default_factory=lambda: str(uuid4()))
