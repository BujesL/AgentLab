from typing import Protocol


class Retriever(Protocol):
    def retrieve(self, query: str, k: int = 3) -> list[str]: ...
