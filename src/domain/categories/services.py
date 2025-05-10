from src.domain.categories.models import CategoryInDB
from src.domain.categories.repository import CategoriesCRUD


async def filter_by_ids(ids: list[int]) -> list[CategoryInDB]:
    categories = await CategoriesCRUD().exclude(ids)
    categories.reverse()

    return categories


async def get_all() -> list[CategoryInDB]:
    categories = await CategoriesCRUD().all()
    categories.reverse()

    return categories
