from abc import ABCMeta
from contextlib import suppress
from importlib.util import module_from_spec, spec_from_file_location
from inspect import isclass
from typing import TypeVar

from sobiraka.processing.abstract import Dispatcher
from sobiraka.utils import AbsolutePath


class Plugin(Dispatcher, metaclass=ABCMeta):
    """
    A plugin for Sobiraka.
    """


class Theme(Plugin, metaclass=ABCMeta):
    """
    A theme for Sobiraka.
    """

    def __init__(self, theme_dir: AbsolutePath):
        super().__init__()
        self.theme_dir: AbsolutePath = theme_dir


P = TypeVar('P', bound=Plugin)


def load_plugin(plugin_file: AbsolutePath, base_class: type[P] = Plugin) -> type[P]:
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


T = TypeVar('T', bound=Theme)


def load_theme(theme_dir: AbsolutePath, base_class: type[Theme]) -> T:
    with suppress(FileNotFoundError, AssertionError):
        base_class = load_plugin(theme_dir / 'theme.py', base_class=base_class)
    return base_class(theme_dir)
