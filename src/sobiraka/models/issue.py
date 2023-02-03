from dataclasses import dataclass


class Issue:
    pass


@dataclass(order=True, frozen=True)
class BadLink(Issue):
    target: str

    def __str__(self):
        return f'Bad link: {self.target}'


@dataclass(order=True, frozen=True)
class AmbiguosLink(Issue):
    target: str
    anchor: str

    def __str__(self):
        return f'Ambiguos link: {self.target}#{self.anchor}'