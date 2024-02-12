from __future__ import annotations

from collections import UserList
from dataclasses import dataclass, field

from panflute import Header, stringify


@dataclass(frozen=True)
class Anchor:
    header: Header = field(hash=False)
    identifier: str
    label: str = field(kw_only=True)
    level: int = field(kw_only=True)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {stringify(self.header.content)!r}>'

    @staticmethod
    def from_header(header: Header) -> Anchor:
        return Anchor(header, header.identifier, label=stringify(header), level=header.level)


class Anchors(UserList[Anchor]):
    def __getitem__(self, key: int | str) -> Anchor:
        match key:
            case int() as index:
                return super().__getitem__(index)
            case str() as identifier:
                return self.by_identifier(identifier)
        raise KeyError(key)

    def by_identifier(self, identifier: str) -> Anchor:
        found: list[Anchor] = []
        for anchor in self.data:
            if anchor.identifier == identifier:
                found.append(anchor)
        assert len(found) == 1, KeyError(identifier)
        return found[0]

    def by_header(self, header: Header) -> Anchor:
        for anchor in self.data:
            if anchor.header is header:
                return anchor
        raise KeyError(header)
