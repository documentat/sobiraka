from dataclasses import dataclass, field
from typing import Sequence

from sobiraka.models import NamingScheme
from sobiraka.utils import RelativePath


@dataclass(kw_only=True, frozen=True)
class Config_Paths:
    """Settings that affect discovering source files."""

    root: RelativePath = None
    """Absolute path to the directory containing the documentation sources."""

    include: Sequence[str] = ('**/*',)
    """
    Patterns used to find source files within the :data:`root`.
    Must be compatible with :py:meth:`Path.glob() <pathlib.Path.glob()>`.
    """

    exclude: Sequence[str] = ()
    """
    Patterns used to exclude certain files within the :data:`root` from the sources.
    Must be compatible with :py:meth:`Path.glob() <pathlib.Path.glob()>`.
    """

    naming_scheme: NamingScheme = field(default_factory=NamingScheme)

    resources: RelativePath | None = None
    """Absolute path to the directory containing the resources, such as images."""

    partials: RelativePath | None = None
    """Absolute path to the directory containing partials that can be included into pages."""
