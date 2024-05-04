
from typing import TypeVar


T = TypeVar('T')

def divide_chunks(list: "list[T]", size: int) -> "list[list[T]]":
    for i in range(0, len(list), size):
        yield list[i:i+size]