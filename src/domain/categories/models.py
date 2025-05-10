from src.infrastructure.models import InternalModel


class CategoryUncommited(InternalModel):
    name: str


class CategoryInDB(CategoryUncommited):
    id: int
