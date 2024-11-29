from __future__ import annotations

from enum import Enum


class CombinedToc(Enum):
    NEVER = 'never'
    CURRENT = 'current'
    ALWAYS = 'always'

    @classmethod
    def from_bool(cls, value: bool) -> CombinedToc:
        if value:
            return CombinedToc.ALWAYS
        return CombinedToc.NEVER
