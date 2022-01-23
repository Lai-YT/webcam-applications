import heapq
from typing import Generic, List, Optional, TypeVar


T = TypeVar("T")

class MinHeap(Generic[T]):
    def __init__(self, items: Optional[List[T]] = None) -> None:
        if not items:
            items = []
        heapq.heapify(items)
        self._heap: List[T] = items

    def push(self, item: T) -> None:
        """Pushes the value item onto the heap."""
        heapq.heappush(self._heap, item)

    def pop(self) -> T:
        """Pops and returns the smallest item from the heap."""
        return heapq.heappop(self._heap)

    @property
    def min(self) -> T:
        """Checks the min value without popping."""
        return self._heap[0]

    def __len__(self) -> int:
        return len(self._heap)

    def __str__(self) -> str:
        return str(self._heap)
