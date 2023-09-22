from abc import ABCMeta
from importlib.util import module_from_spec, spec_from_file_location
from inspect import isclass
from pathlib import Path
from typing import TypeVar

from sobiraka.processing.abstract import Dispatcher


class Plugin(Dispatcher, metaclass=ABCMeta):
    """
    A plugin for Sobiraka.
    """


P = TypeVar('P', bound=Plugin)


def load_plugin(plugin_file: Path, base_class: type[P] = Plugin) -> type[P]:
    """
    Attempt to load a Plugin from given `plugin_file`.

    Note that the file may contain more than one class,
    but the function will make sure that only one class is based on the given `base_class`.

    The function returns the found class (not an instance).
    """
    module_spec = spec_from_file_location('plugin', plugin_file)
    module = module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    klasses = []
    for klass_name, klass in module.__dict__.items():
        if not klass_name.startswith('__'):
            if isclass(klass) and issubclass(klass, base_class):
                if klass is not base_class:
                    klasses.append(klass)
    assert len(klasses) == 1, klasses
    klass = klasses[0]
    return klass
