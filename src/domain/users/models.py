from src.domain.configurations import Configuration
from src.infrastructure.models import InternalModel

__all__ = ("UserUncommited", "UserInDB", "User")


class UserUncommited(InternalModel):
    account_id: int
    chat_id: int
    username: str
    full_name: str


class UserInDB(UserUncommited):
    id: int


class User(UserInDB):

    configuration: Configuration
    class Config:
        from_attributes = True

