from dataclasses import dataclass


class ProcessingError:
    pass


@dataclass(order=True, frozen=True)
class BadLinkError(ProcessingError):
    target: str

    def __str__(self):
        return f'Bad link: {self.target}'