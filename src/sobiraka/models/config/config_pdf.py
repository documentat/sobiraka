from dataclasses import dataclass
from importlib.resources import files
from math import inf

from sobiraka.utils import AbsolutePath, RelativePath


@dataclass(kw_only=True, frozen=True)
class Config_PDF:
    """Settings related to :class:`.WeasyBuilder`."""

    theme: AbsolutePath = files('sobiraka') / 'files' / 'themes' / 'printable'
    """Path to the theme that should be used when generating PDF via WeasyPrint."""

    processor: RelativePath = None
    """Path to the custom Processor implementation."""

    custom_styles: tuple[RelativePath, ...] = ()

    toc_depth: int | float = inf

    combined_toc: bool = False
