from operator import getitem
from typing import Generator, Iterable, Sequence, TypeVar

from src.infrastructure.models import InternalModel


def list_by_chunks(data: list, size: int = 2) -> Generator:
    for i in range(0, len(data), size):
        yield data[i : i + size]


_Member = TypeVar("_Member", bound=(InternalModel | dict))


def build_dict_from_sequence(
    seq: Iterable[_Member], key: str
) -> dict[str, _Member]:

    if not seq or not isinstance(seq, Sequence):
        return {}

    if isinstance(seq[0], dict):
        return {getitem(item, key): item for item in seq}  # type: ignore

    if isinstance(seq[0], InternalModel):
        return {getattr(element, key): element for element in seq}

    raise ValueError("Unsupported type for build operation")


def without_duplicates(sequence: Iterable) -> Generator:
    data = set()

    for el in sequence:
        if el not in data:
            yield el
            data.add(el)
        continue
