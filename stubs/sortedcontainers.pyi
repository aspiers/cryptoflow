from typing import Generic, Iterator, TypeVar


_T = TypeVar('_T')
_SortedSetT = TypeVar("_SortedSetT")


class SortedSet(Generic[_T]):
    def add(self, t: _T): ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[_T]: ...
    def __getitem__(self: _SortedSetT, s: slice) -> _SortedSetT: ...
