from dataclasses import dataclass, field
from math import inf
from typing import Literal

from sobiraka.utils import RelativePath
from .config_highlight import Config_Pdf_Highlight
from .config_utils import Config_Theme


@dataclass(kw_only=True, frozen=True)
class Config_PDF:
    """Settings related to :class:`.WeasyPrintBuilder`."""

    theme: Config_Theme = field(default_factory=lambda: Config_Theme.from_name('sobiraka2025'))

    processor: RelativePath = None
    """Path to the custom Processor implementation."""

    custom_styles: tuple[RelativePath, ...] = ()

    toc_depth: int | float = inf

    combined_toc: bool = False

    headers_policy: Literal['local', 'global'] = 'local'

    highlight: Config_Pdf_Highlight = None
