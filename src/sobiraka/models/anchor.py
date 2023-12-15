from __future__ import annotations

from dataclasses import dataclass, field

from panflute import Header, stringify

from sobiraka.utils import TocNumber


@dataclass
class Anchor:
    header: Header
    identifier: str
    label: str = field(kw_only=True)
    level: int = field(kw_only=True)
    number: TocNumber = field(init=False, default=None)

    @staticmethod
    def from_header(header: Header) -> Anchor:
        return Anchor(header, header.identifier, label=stringify(header), level=header.level)


class Anchors(list[Anchor]):
    def __getitem__(self, identifier: str) -> Anchor:
        found: list[Anchor] = []
        for anchor in self:
            if anchor.identifier == identifier:
                found.append(anchor)
        assert len(found) == 1, KeyError(identifier)
        return found[0]

    def by_header(self, header: Header) -> Anchor:
        for anchor in self:
            if anchor.header is header:
                return anchor
        raise KeyError(header)
