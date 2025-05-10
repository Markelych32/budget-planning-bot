from src.domain.configurations import services as configuration_service
from src.domain.users.models import UserInDB, UserUncommited
from src.domain.users.repository import UsersCRUD


async def create_user(schema: UserUncommited) -> UserInDB:

    user: UserInDB = await UsersCRUD().create(schema)
    await configuration_service.create_default(user_id=user.id)

    return user
