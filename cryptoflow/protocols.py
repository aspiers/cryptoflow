#!/usr/bin/env python3

from typing_extensions import Protocol


class SupportsWrite(Protocol):
    def write(self, s: str) -> int:
        pass
