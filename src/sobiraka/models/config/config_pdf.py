from dataclasses import dataclass
from importlib.resources import files
from math import inf
from typing import Literal

from sobiraka.utils import AbsolutePath, RelativePath
from .config_highlight import Config_Pdf_Highlight


@dataclass(kw_only=True, frozen=True)
class Config_PDF:
    """Settings related to :class:`.WeasyPrintBuilder`."""

    theme: AbsolutePath = AbsolutePath(files('sobiraka')) / 'files' / 'themes' / 'sobiraka2025'
    """Path to the theme that should be used when generating PDF via WeasyPrint."""

    processor: RelativePath = None
    """Path to the custom Processor implementation."""

    custom_styles: tuple[RelativePath, ...] = ()

    toc_depth: int | float = inf

    combined_toc: bool = False

    headers_policy: Literal['local', 'global'] = 'local'

    highlight: Config_Pdf_Highlight = None
