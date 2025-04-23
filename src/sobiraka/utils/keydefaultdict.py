from typing import Callable, Generic, TypeVar

K = TypeVar('K')
V = TypeVar('V')


class KeyDefaultDict(dict[K, V], Generic[K, V]):
    def __init__(self, default_factory: Callable[[K], V]):
        self.default_factory = default_factory
        super().__init__()

    def __missing__(self, key: K) -> V:
        value = self.default_factory(key)
        self[key] = value
        return value
