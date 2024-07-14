from typing import Any, Callable, TypeVar

K = TypeVar('K')
V = TypeVar('V')


def sorted_dict(data: dict[K, V], key: Callable[[K], Any] = lambda k: k) -> dict[K, V]:
    return dict(sorted(data.items(), key=lambda kv: key(kv[0])))
