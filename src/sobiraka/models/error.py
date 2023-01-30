from dataclasses import dataclass


class ProcessingError:
    pass


@dataclass(order=True, frozen=True)
class BadLinkError(ProcessingError):
    target: str

    def __str__(self):
        return f'Bad link: {self.target}'


@dataclass(order=True, frozen=True)
class AmbiguosLinkError(ProcessingError):
    target: str
    anchor: str

    def __str__(self):
        return f'Ambiguos link: {self.target}#{self.anchor}'