from __future__ import annotations

import json
from copy import copy
from dataclasses import asdict, dataclass, field
from enum import Enum
from importlib.resources import files
from math import inf
from typing import Any

from panflute import Element
from utilspie.collectionsutils import frozendict

from sobiraka.models import NamingScheme
from sobiraka.utils import AbsolutePath, RelativePath


@dataclass(kw_only=True, frozen=True)
class Config_Paths:
    """Settings that affect discovering source files."""

    root: RelativePath = None
    """Absolute path to the directory containing the documentation sources."""

    include: tuple[str] = ('**/*',)
    """
    Patterns used to find source files within the :data:`root`.
    Must be compatible with :py:meth:`Path.glob() <pathlib.Path.glob()>`.
    """

    exclude: tuple[str] = ()
    """
    Patterns used to exclude certain files within the :data:`root` from the sources.
    Must be compatible with :py:meth:`Path.glob() <pathlib.Path.glob()>`.
    """

    naming_scheme: NamingScheme = field(default_factory=NamingScheme)

    resources: RelativePath | None = None
    """Absolute path to the directory containing the resources, such as images."""

    partials: RelativePath | None = None
    """Absolute path to the directory containing partials that can be included into pages."""


@dataclass(kw_only=True, frozen=True)
class Config_Content:
    """Format-agnostic content settings."""

    numeration: bool = False
    """Whether to add automatic numbers to all the headers."""


class CombinedToc(Enum):
    NEVER = 'never'
    CURRENT = 'current'
    ALWAYS = 'always'

    @classmethod
    def from_bool(cls, value: bool) -> CombinedToc:
        if value:
            return CombinedToc.ALWAYS
        return CombinedToc.NEVER


class SearchIndexerName(Enum):
    PAGEFIND = 'pagefind'


class Config_Search_LinkTarget(Enum):
    H1 = 'h1'
    H2 = 'h2'
    H3 = 'h3'
    H4 = 'h4'
    H5 = 'h5'
    H6 = 'h6'

    @property
    def level(self) -> int:
        return int(self.value[-1])


@dataclass(kw_only=True, frozen=True)
class Config_Pagefind_Translations:
    # pylint: disable=too-many-instance-attributes
    placeholder: str = None
    clear_search: str = None
    load_more: str = None
    search_label: str = None
    filters_label: str = None
    zero_results: str = None
    many_results: str = None
    one_result: str = None
    alt_search: str = None
    search_suggestion: str = None
    searching: str = None

    def to_json(self) -> str:
        """
        Returns a JSON object with all non-empty translations.
        """
        translations = asdict(self)
        for key, value in copy(translations).items():
            if value is None:
                del translations[key]
        return json.dumps(translations, ensure_ascii=False)


@dataclass(kw_only=True, frozen=True)
class Config_Web_Search:
    engine: SearchIndexerName = None
    index_path: str = None
    skip_elements: tuple[type[Element], ...] = ()
    link_target: Config_Search_LinkTarget = Config_Search_LinkTarget.H1
    translations: Config_Pagefind_Translations = field(default_factory=Config_Pagefind_Translations)


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

    theme: AbsolutePath = files('sobiraka') / 'files' / 'themes' / 'simple'
    """Path to the theme that should be used when generating HTML."""

    theme_data: dict[str, Any] = field(default=dict)

    toc_depth: int | float = inf

    combined_toc: CombinedToc = CombinedToc.NEVER

    search: Config_Web_Search = field(default_factory=Config_Web_Search)


@dataclass(kw_only=True, frozen=True)
class Config_Latex:
    """Settings related to :class:`.LatexBuilder`."""

    header: RelativePath | None = None
    """Path to the file containing LaTeX header directives for the volume, if provided."""

    theme: AbsolutePath = None
    """Path to the theme that should be used when generating LaTeX."""

    toc: bool = True
    """Whether to add a table of contents."""

    paths: dict[str, RelativePath] = field(default=dict)


@dataclass(kw_only=True, frozen=True)
class Config_WeasyPrint:
    """Settings related to :class:`.WeasyBuilder`."""

    theme: AbsolutePath = files('sobiraka') / 'files' / 'themes' / 'printable'
    """Path to the theme that should be used when generating PDF via WeasyPrint."""

    toc_depth: int | float = inf

    combined_toc: bool = False


@dataclass(kw_only=True, frozen=True)
class Config_Lint_Checks:
    """Boolean options representing enabled and disabled checks that should be performed when linting."""

    phrases_must_begin_with_capitals: bool = True
    """
    For each phrase in the text, check that its first character is a lowercase letter, unless:
    
    - the phrase is inside a code span or a code block,
    - the phrase is an item's first phrase in a list that is preceded by a colon.
    """


@dataclass(kw_only=True, frozen=True)
class Config_Lint:
    """Settings related to :class:`.Linter`."""

    dictionaries: tuple[str, ...] = ()
    """
    The Hunspell dictionaries to use for spellchecking.
    
    This may include both the names of the dictionaries available in the environment (e.g., ``en_US``)
    and relative paths to specific dictionaries present under the project root.
    """

    exceptions: tuple[RelativePath, ...] = ()
    """
    Relative paths to the files containing word and phrases that should not be treated as incorrect.
    
    See :func:`.exceptions_regexp()`.
    """

    checks: Config_Lint_Checks = None
    """Additional checks enabled for this volume."""


@dataclass(kw_only=True, frozen=True)
class Config:
    """
    Configuration for a volume. Used as a base class for :obj:`.Volume`.
    """
    # pylint: disable=too-many-instance-attributes

    title: str = None

    paths: Config_Paths = field(default_factory=Config_Paths, kw_only=True)
    """Settings that affect discovering source files."""

    web: Config_Web = field(default_factory=Config_Web, kw_only=True)
    """Settings related to :class:`.WebBuilder`."""

    content: Config_Content = field(default=Config_Content, kw_only=True)

    latex: Config_Latex = field(default_factory=Config_Latex, kw_only=True)
    """Settings related to :class:`.LatexBuilder`."""

    weasyprint: Config_WeasyPrint = field(default=Config_WeasyPrint, kw_only=True)
    """Settings related to :class:`.WeasyBuilder`."""

    lint: Config_Lint = field(default_factory=Config_Lint, kw_only=True)
    """Settings related to :class:`.Linter`."""

    variables: dict[str, Any] = field(default_factory=frozendict, kw_only=True)
    """Arbitrary variables that can be passed to the template engine."""
