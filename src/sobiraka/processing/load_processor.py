import inspect
import sys
from contextlib import suppress
from importlib.util import module_from_spec, spec_from_file_location
from inspect import isclass
from typing import TypeVar

from sobiraka.processing.abstract.processor import Processor
from sobiraka.utils import AbsolutePath

P = TypeVar('P', bound=Processor)


def load_processor(custom_processor_file: AbsolutePath, theme_dir: AbsolutePath, base_class: type[P]) -> type[P]:
    """
    Load a processor class from one of two places:

    - a file specified in `custom_custom_processor_file` (CAN exist, MUST exist and be loadable if specified),
    - a file inside `theme_dir` (CAN exist, CAN be loadable, must be the only such class there if loadable)
    """
    if custom_processor_file:
        return _load_processor_from_file(custom_processor_file, base_class)
    with suppress(ExtensionFileNotFound, ClassNotFound):
        return _load_processor_from_file(theme_dir / 'extension.py', base_class)
    return base_class


def _load_processor_from_file(extension_file: AbsolutePath, base_class: type[P]) -> type[P]:
    # Load the file
    if not extension_file.exists():
        raise ExtensionFileNotFound
    module_spec = spec_from_file_location('extension', extension_file)
    module = module_from_spec(module_spec)
    sys.modules['extension'] = module
    module_spec.loader.exec_module(module)

    # Find the class that extends the base class
    klasses = []
    for _, klass in inspect.getmembers(module):
        with suppress(AssertionError, TypeError):
            assert inspect.getfile(klass) == str(extension_file)
            assert isclass(klass)
            assert issubclass(klass, base_class)
            klasses.append(klass)

    # Make sure there is one and only one such class
    if len(klasses) != 1:
        raise ClassNotFound
    klass = klasses[0]

    return klass


class ExtensionFileNotFound(Exception):
    pass


class ClassNotFound(Exception):
    pass
