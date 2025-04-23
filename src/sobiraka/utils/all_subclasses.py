from typing import Iterable, TypeVar

T = TypeVar('T')


def all_subclasses(klass: type[T]) -> Iterable[type[T]]:
    for subclass in klass.__subclasses__():
        yield subclass
        yield from all_subclasses(subclass)
