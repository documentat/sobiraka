from dataclasses import dataclass, field
from math import inf
from typing import Any

from utilspie.collectionsutils import frozendict

from sobiraka.utils import RelativePath
from .config_highlight import Config_Web_Highlight
from .config_search import Config_Web_Search
from .config_utils import CombinedToc, Config_Theme


@dataclass(kw_only=True, frozen=True)
class Config_Web:
    """Settings related to :class:`.WebBuilder`."""

    # pylint: disable=too-many-instance-attributes

    prefix: str = '$AUTOPREFIX'
    """
    Relative path to the directory for placing the HTML files.
    
    The following variables can be used in the string:
    
    - ``$LANG`` — will be replaced with :obj:`.Volume.lang` (or ``''``, if not set).
    - ``$VOLUME`` — will be replaced with :obj:`.Volume.codename`,
    - ``$AUTOPREFIX`` — will be replaced with :obj:`.Volume.autoprefix`.
    """

    resources_prefix: str = '_resources'
    """Relative path to the directory for placing the resources, such as images."""

    resources_force_copy: tuple[str, ...] = ()

    theme: Config_Theme = field(default_factory=lambda: Config_Theme.from_name('book'))

    theme_data: dict[str, Any] = field(default=frozendict)

    processor: RelativePath = None
    """Path to the custom Processor implementation."""

    custom_styles: tuple[RelativePath, ...] = ()

    custom_scripts: tuple[RelativePath, ...] = ()

    toc_depth: int | float = inf

    combined_toc: CombinedToc = CombinedToc.NEVER

    search: Config_Web_Search = field(default_factory=Config_Web_Search)

    highlight: Config_Web_Highlight = None
