from dataclasses import fields, is_dataclass


def get_default(klass, field_name: str):
    assert is_dataclass(klass)
    for field in fields(klass):
        if field.name == field_name:
            return field.default
    raise KeyError(field_name)
