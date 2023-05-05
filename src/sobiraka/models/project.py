from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Iterable, TYPE_CHECKING

import jsonschema
import yaml
from more_itertools import unique_justseen
from utilspie.collectionsutils import frozendict

from sobiraka.runtime import RT

if TYPE_CHECKING: from .page import Page

MANIFEST_SCHEMA = yaml.load((RT.FILES / 'sobiraka-project.yaml').read_text(), yaml.SafeLoader)


@dataclass(kw_only=True, frozen=True)
class Volume_Paths:
    root: Path
    resources: Path
    include: tuple[str]
    exclude: tuple[str]


@dataclass(kw_only=True, frozen=True)
class Volume_HTML:
    resources_prefix: Path | None = None


@dataclass(kw_only=True, frozen=True)
class Volume_PDF:
    header: Path | None = None
    """Path to the file containing LaTeX header directives for the book, if provided."""


@dataclass(kw_only=True, frozen=True)
class Volume_Lint_Checks:
    phrases_must_begin_with_capitals: bool = True


@dataclass(kw_only=True, frozen=True)
class Volume_Lint:
    dictionaries: tuple[str, ...]
    """List of Hunspell dictionaries to use for spellchecking."""

    exceptions: tuple[Path]

    checks: Volume_Lint_Checks


@dataclass(kw_only=True, frozen=True)
class Volume:
    project: Project = field(init=False, hash=False)
    lang: str | None = None
    codename: str = ''

    title: str = ''
    """Book title. May be used when rendering output files."""

    paths: Volume_Paths = field(default_factory=Volume_Paths, kw_only=True)
    html: Volume_HTML = field(default_factory=Volume_HTML, kw_only=True)
    pdf: Volume_PDF = field(default_factory=Volume_PDF, kw_only=True)
    lint: Volume_Lint = field(default_factory=Volume_Lint, kw_only=True)
    variables: dict[str, Any] = field(default_factory=frozendict, kw_only=True)

    def __hash__(self):
        return hash((id(self.project), self.codename, self.lang))

    def __repr__(self):
        return f'<{self.__class__.__name__}: {repr(str(self.paths.root))}>'

    @cached_property
    def pages_by_path(self) -> dict[Path, Page]:
        from .page import Page
        from .emptypage import EmptyPage

        pages: list[Page] = []
        pages_by_path: dict[Path, Page] = {}
        expected_paths: set[Path] = set()

        paths: set[Path] = set()
        for pattern in self.paths.include:
            paths |= set(self.root.glob(pattern))
        for pattern in self.paths.exclude:
            paths -= set(self.root.glob(pattern))

        for path in paths:
            relative_path = path.relative_to(self.root)
            absolute_path = path.resolve()

            page = Page(self, absolute_path)
            pages.append(page)
            pages_by_path[relative_path] = page
            if page.is_index:
                pages_by_path[relative_path.parent] = page
                expected_paths |= set(relative_path.parent.parents)
            else:
                expected_paths |= set(relative_path.parents)

        for expected_path in expected_paths:
            if expected_path not in pages_by_path:
                page = EmptyPage(self, self.root / expected_path)
                pages.append(page)
                pages_by_path[expected_path] = page

        return frozendict(sorted(pages_by_path.items()))

    @property
    def pages(self) -> tuple[Page, ...]:
        pages = sorted(self.pages_by_path.values(), key=lambda p: p.path)
        pages = list(unique_justseen(pages))
        return tuple(pages)

    @property
    def root(self) -> Path:
        """Absolute path to the root directory of the book."""
        return self.paths.root

    @cached_property
    def max_level(self) -> int:
        """Maximum value of :obj:`.Page.level` in the book. Used for calculating :obj:`.Page.antilevel`."""
        levels = tuple(page.level for page in self.pages)
        return max(levels) if levels else 0


@dataclass(kw_only=True, frozen=True)
class Project:
    """
    A single documentation project that needs to be processed and rendered.

    .. important::
        Note that because each :class:`.Page`'s data is modified during processing, a book must not be used for more than one rendering.
        Doing so will lead to unexpected behavior, as data loaded with different parameters do not necessarily co-exist nnicely.
    """
    root: Path

    volumes: tuple[Volume, ...] = field(hash=False)
    volumes_by_key: dict[str | None, Volume] = field(hash=False)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.root)!r}>'

    @cached_property
    def pages_by_path(self) -> dict[Path, Page]:
        pages_by_path = {}
        for volume in self.volumes:
            pages_by_path |= volume.pages_by_path
        return frozendict(pages_by_path)

    @property
    def pages(self) -> tuple[Page, ...]:
        pages = sorted(self.pages_by_path.values(), key=lambda p: p.path)
        pages = list(unique_justseen(pages))
        return tuple(pages)


def load_project(manifest_path: Path) -> Project:
    manifest_path = manifest_path.resolve()
    with manifest_path.open() as manifest_file:
        manifest: dict = yaml.safe_load(manifest_file) or {}
    return load_project_from_dict(manifest, base=manifest_path.parent)


def load_project_from_dict(manifest: dict, *, base: Path) -> Project:
    if manifest:
        jsonschema.validate(manifest, MANIFEST_SCHEMA)

    volumes: list[Volume] = []
    volumes_by_key: dict[str | None, Volume] = {}

    for lang, language_data in _normalized_and_merged(manifest, 'languages'):
        for codename, volume_data in _normalized_and_merged(language_data, 'volumes'):
            volume = _load_volume(lang, codename, volume_data, base)
            key = '/'.join(filter(None, (lang, codename))) or None
            volumes.append(volume)
            volumes_by_key[key] = volume

    project = Project(root=base, volumes=tuple(volumes), volumes_by_key=frozendict(volumes_by_key))
    for volume in volumes:
        object.__setattr__(volume, 'project', project)
    return project


def _normalized_and_merged(data: dict, key: str) -> Iterable[tuple[str, dict]]:
    from sobiraka.utils import merge_dicts

    if key not in data:
        yield None, data
    elif list(data[key]) == ['_']:
        yield None, data[key]['_']
    elif '_' in data[key]:
        defaults = data[key].pop('_')
        for k, v in data[key].items():
            v = merge_dicts(defaults, v)
            yield k, v
    else:
        yield from data[key].items()


def _load_volume(lang: str | None, codename: str, volume_data: dict, base: Path) -> Volume:
    from sobiraka.utils import convert_or_none

    def _(_keys, _default=None):
        try:
            _result = volume_data
            for key in _keys.split('.'):
                _result = _result[key]
            return _result
        except KeyError:
            return _default

    def global_path(x: str) -> Path:
        return (base / (x or '')).resolve()

    return Volume(
        codename=codename,
        lang=lang,
        title=_('title'),
        paths=Volume_Paths(
            root=global_path(_('paths.root')),
            resources=global_path(_('paths.resources')),
            include=tuple(_('paths.include', ['**/*'])),
            exclude=tuple(_('paths.exclude', '')),
        ),
        html=Volume_HTML(
            resources_prefix=convert_or_none(global_path, _('html.resources_prefix', '_resources')),
        ),
        pdf=Volume_PDF(
            header=convert_or_none(global_path, _('pdf.header')),
        ),
        lint=Volume_Lint(
            dictionaries=tuple(_('lint.dictionaries', [])),
            exceptions=tuple(global_path(x) for x in _('lint.exceptions', [])),
            checks=Volume_Lint_Checks(**_('lint.checks', {})),
        ),
        variables=frozendict(_('variables', {})),
    )