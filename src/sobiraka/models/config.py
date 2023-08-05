from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from utilspie.collectionsutils import frozendict

from sobiraka.models import NamingScheme
from sobiraka.runtime import RT


@dataclass(kw_only=True, frozen=True)
class Config_Paths:
    """Settings that affect discovering source files."""

    root: Path = None
    """Absolute path to the directory containing the documentation sources."""

    resources: Path | None = None
    """Absolute path to the directory containing the resources, such as images."""

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

    naming_scheme: NamingScheme = NamingScheme()


@dataclass(kw_only=True, frozen=True)
class Config_HTML:
    """Settings related to :class:`.HtmlBuilder`."""

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

    theme: Path = RT.FILES / 'themes' / 'simple'
    # TODO: describe what should be there

    theme_data: dict[str, Any] = field(default=dict)


@dataclass(kw_only=True, frozen=True)
class Config_PDF:
    """Settings related to :class:`.PdfBuilder`."""

    header: Path | None = None
    """Path to the file containing LaTeX header directives for the volume, if provided."""


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

    exceptions: tuple[Path] = ()
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
    title: str = None

    paths: Config_Paths = field(default_factory=Config_Paths, kw_only=True)
    """Settings that affect discovering source files."""

    html: Config_HTML = field(default_factory=Config_HTML, kw_only=True)
    """Settings related to :class:`.HtmlBuilder`."""

    pdf: Config_PDF = field(default_factory=Config_PDF, kw_only=True)
    """Settings related to :class:`.PdfBuilder`."""

    lint: Config_Lint = field(default_factory=Config_Lint, kw_only=True)
    """Settings related to :class:`.Linter`."""

    variables: dict[str, Any] = field(default_factory=frozendict, kw_only=True)
    """Arbitrary variables that can be passed to the template engine."""
