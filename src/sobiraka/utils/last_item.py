import dataclasses
from typing import TypeVar

K = TypeVar('K')
V = TypeVar('V')


def last_key(data: dict[K, V]) -> K:
    return list(data.keys())[-1]


def last_value(data: dict[K, V]) -> V:
    return list(data.values())[-1]


def last_item(data: dict[K, V]) -> tuple[K, V]:
    return list(data.items())[-1]


def update_last_value(data: dict[K, V], value: V):
    data[last_key(data)] = value


def update_last_dataclass(data: dict[K, V], **changes):
    key, value = last_item(data)
    value = dataclasses.replace(value, **changes)
    data[key] = value
