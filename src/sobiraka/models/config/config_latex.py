from contextlib import suppress
from dataclasses import dataclass, field
from importlib.resources import files
from typing import Self

from utilspie.collectionsutils import frozendict

from sobiraka.utils import AbsolutePath, RelativePath


@dataclass(kw_only=True, frozen=True)
class Config_Latex_HeadersTransform:
    by_class: dict[str, str] = field(default_factory=frozendict)
    by_global_level: dict[int, str] = field(default_factory=lambda: frozendict({
        1: 'part*',
        2: 'section*',
        3: 'subsection*',
        4: 'subsubsection*',
        5: 'paragraph*',
        6: 'subparagraph*',
    }))
    by_page_level: dict[int, str] = field(default_factory=frozendict)
    by_element: dict[int, str] = field(default_factory=frozendict)

    @classmethod
    def load(cls, data: dict) -> Self:
        kwargs = dict()
        with suppress(KeyError):
            kwargs['by_class'] = frozendict(data['by_class'])
        with suppress(KeyError):
            kwargs['by_global_level'] = frozendict({int(k): v for k, v in data['by_global_level'].items()})
        with suppress(KeyError):
            kwargs['by_page_level'] = frozendict({int(k): v for k, v in data['by_page_level'].items()})
        with suppress(KeyError):
            kwargs['by_element'] = frozendict(data['by_element'])
        return cls(**kwargs)


@dataclass(kw_only=True, frozen=True)
class Config_Latex:
    """Settings related to :class:`.LatexBuilder`."""

    header: RelativePath | None = None
    """Path to the file containing LaTeX header directives for the document, if provided."""

    theme: AbsolutePath = AbsolutePath(files('sobiraka')) / 'files' / 'themes' / 'simple'
    """Path to the theme that should be used when generating LaTeX."""

    processor: RelativePath = None
    """Path to the custom Processor implementation."""

    toc: bool = True
    """Whether to add a table of contents."""

    paths: dict[str, RelativePath] = field(default=frozendict)

    headers_transform: Config_Latex_HeadersTransform = field(default_factory=Config_Latex_HeadersTransform)
