from abc import ABCMeta
from importlib.util import module_from_spec, spec_from_file_location
from inspect import isclass
from pathlib import Path
from typing import TypeVar

from sobiraka.processing.abstract import Dispatcher


class Plugin(Dispatcher, metaclass=ABCMeta):
    pass


P = TypeVar('P', bound=Plugin)


def load_plugin(plugin_file: Path, base_class: type[P] = Plugin) -> type[P]:
    module_spec = spec_from_file_location('plugin', plugin_file)
    module = module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    klasses = []
    for klass_name, klass in module.__dict__.items():
        if not klass_name.startswith('__'):
            if isclass(klass) and issubclass(klass, base_class):
                if klass is not base_class:
                    klasses.append(klass)
    assert len(klasses) == 1
    klass = klasses[0]
    return klass
