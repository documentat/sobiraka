from dataclasses import dataclass, field

from utilspie.collectionsutils import frozendict

from sobiraka.utils import AbsolutePath, RelativePath


@dataclass(kw_only=True, frozen=True)
class Config_Latex_Headers:
    by_class: dict[str, str] = field(default_factory=frozendict)
    by_global_level: dict[int, str] = field(default=frozendict({
        1: 'part*',
        2: 'section*',
        3: 'subsection*',
        4: 'subsubsection*',
        5: 'paragraph*',
        6: 'subparagraph*',
    }))
    by_page_level: dict[int, str] = field(default_factory=frozendict)
    by_element: dict[int, str] = field(default_factory=frozendict)


@dataclass(kw_only=True, frozen=True)
class Config_Latex:
    """Settings related to :class:`.LatexBuilder`."""

    header: RelativePath | None = None
    """Path to the file containing LaTeX header directives for the volume, if provided."""

    theme: AbsolutePath = None
    """Path to the theme that should be used when generating LaTeX."""

    processor: RelativePath = None
    """Path to the custom Processor implementation."""

    toc: bool = True
    """Whether to add a table of contents."""

    paths: dict[str, RelativePath] = field(default=frozendict)

    headers: Config_Latex_Headers = field(default_factory=Config_Latex_Headers)
