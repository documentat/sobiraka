from dataclasses import dataclass


@dataclass(frozen=True)
class Anchor:
    identifier: str
    label: str
    level: int


class Anchors(list[Anchor]):
    def __getitem__(self, identifier: str) -> Anchor:
        found: list[Anchor] = []
        for anchor in self:
            if anchor.identifier == identifier:
                found.append(anchor)
        assert len(found) == 1, KeyError(identifier)
        return found[0]
