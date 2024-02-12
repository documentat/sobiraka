from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cached_property
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, overload

import yaml

from ..syntax import Syntax
from ..version import TranslationStatus, Version

if TYPE_CHECKING:
    from sobiraka.models.volume import Volume

_META_PATTERN = re.compile(r'^---\n(.+\n)?---\n', re.DOTALL)


class Page:
    """
    Representation of a single source file in the documentation.

    During the processing by the :func:`.load_page()`, :func:`.process1()` and :func:`.process2()` functions,
    some of the page's fields may be altered.
    """

    @overload
    def __init__(self, volume: Volume, path_in_volume: Path, /):
        ...

    @overload
    def __init__(self, volume: Volume, path_in_volume: Path, meta: PageMeta, text: str, /):
        ...

    @overload
    def __init__(self, volume: Volume, path_in_volume: Path, raw_text: str, /):
        ...

    @overload
    def __init__(self, path_in_volume: Path, /):
        ...

    @overload
    def __init__(self, path_in_volume: Path, meta: PageMeta, text: str, /):
        ...

    @overload
    def __init__(self, path_in_volume: Path, raw_text: str, /):
        ...

    @overload
    def __init__(self, meta: PageMeta, text: str, /):
        ...

    @overload
    def __init__(self, raw_text: str = '', /):
        ...

    def __init__(self, *args):
        from sobiraka.models.volume import Volume

        self.volume: Volume | None = None
        self.path_in_volume: Path | None = None

        self.__meta: PageMeta | None = None
        self.__text: str | None = None

        match args:
            case Volume() as volume, Path() as path_in_volume:
                self.volume = volume
                self.path_in_volume = path_in_volume

            case Volume() as volume, Path() as path_in_volume, PageMeta() as meta, str() as text:
                self.volume = volume
                self.path_in_volume = path_in_volume
                self.__meta = meta
                self.__text = text

            case Volume() as volume, Path() as path_in_volume, str() as raw_text:
                self.volume = volume
                self.path_in_volume = path_in_volume
                self._process_raw(raw_text)

            case Path() as path_in_volume,:
                self.path_in_volume = path_in_volume

            case Path() as path_in_volume, PageMeta() as meta, str() as text:
                self.path_in_volume = path_in_volume
                self.__meta = meta
                self.__text = text

            case Path() as path_in_volume, str() as raw_text:
                self.path_in_volume = path_in_volume
                self._process_raw(raw_text)

            case str() as raw_text,:
                self._process_raw(raw_text)

            case PageMeta() as meta, str() as text:
                self.__meta = meta
                self.__text = text

            case ():
                self.__meta = PageMeta()
                self.__text = ''

            case _:
                raise TypeError(*args)

    def __eq__(self, other: Page):
        try:
            assert self.__class__ is other.__class__
            assert self.volume is other.volume
            assert self.path_in_volume == other.path_in_volume
            return True
        except AssertionError:
            return False

    def __hash__(self):
        return hash(id(self))

    def __repr__(self):
        path = '/'.join(self.path_in_volume.parts)
        match path:
            case self.volume.autoprefix:
                return f'<{self.__class__.__name__}: [{self.volume.autoprefix}]/{path}>'
            case Path('.'):
                return f'<{self.__class__.__name__}: />'
            case _:
                return f'<{self.__class__.__name__}: /{path}>'

    def __lt__(self, other):
        assert isinstance(other, Page), TypeError
        assert self.volume.project == other.volume.project
        self_breadcrumbs_as_indexes = tuple(x.index for x in self.breadcrumbs)
        other_breadcrumbs_as_indexes = tuple(x.index for x in other.breadcrumbs)
        return (self.volume, self_breadcrumbs_as_indexes) < (other.volume, other_breadcrumbs_as_indexes)

    # ------------------------------------------------------------------------------------------------------------------
    # Reading the source file

    def _process_raw(self, raw_text: str):
        if m := re.fullmatch(r'--- \n (.+\n)? --- (?: \n+ (.+) )?', raw_text, re.DOTALL | re.VERBOSE):
            if meta_str := m.group(1):
                meta = yaml.safe_load(meta_str)
            else:
                meta = {}
            self.__meta = PageMeta(**meta)
            self.__text = m.group(2)
        else:
            self.__meta = PageMeta()
            self.__text = raw_text

    @property
    def meta(self) -> PageMeta:
        if self.__meta is None:
            raw_text = self.volume.project.fs.read_text(self.path_in_project)
            self._process_raw(raw_text)
        return self.__meta

    @property
    def text(self) -> str:
        if self.__text is None:
            raw_text = self.volume.project.fs.read_text(self.path_in_project)
            self._process_raw(raw_text)
        return self.__text

    @property
    def syntax(self) -> Syntax:
        try:
            return Syntax(self.path_in_volume.suffix[1:])
        except ValueError:
            return Syntax.MD

    # ------------------------------------------------------------------------------------------------------------------
    # Paths and the position in the tree

    @cached_property
    def path_in_project(self) -> Path:
        return self.volume.relative_root / self.path_in_volume

    def is_root(self) -> bool:
        return False

    @cached_property
    def breadcrumbs(self) -> tuple[Page, ...]:
        breadcrumbs: list[Page] = [self]
        while breadcrumbs[0].parent is not None:
            breadcrumbs.insert(0, breadcrumbs[0].parent)
        return tuple(breadcrumbs)

    @cached_property
    def parent(self) -> Page | None:
        if self.is_root():
            return None
        return self.volume.pages_by_path[self.path_in_volume.parent]

    @cached_property
    def children(self) -> tuple[Page, ...]:
        children: list[Page] = []
        for page in self.volume.pages:
            if page.parent is self:
                children.append(page)
        return tuple(children)

    def id_segment(self) -> str:
        if self.is_root():
            return 'r'
        return self.stem

    @property
    def index(self) -> int | float:
        return self.volume.config.paths.naming_scheme.get_index(self.path_in_project)

    @property
    def stem(self) -> str:
        return self.volume.config.paths.naming_scheme.get_stem(self.path_in_project)

    @cached_property
    def id(self) -> str:
        """
        Textual representation of :data:`breadcrumbs`, unique within the :class:`.Volume`.

        :examples:
            ``0-main.md`` → ``r`` \n
            ``2-company/5-about/0-index.md`` → ``r--company--about`` \n
            ``2-company/5-about/1-contacts.md`` → ``r--company--about--contacts``
        """
        parts: list[str] = []
        for page in self.breadcrumbs:
            parts.append(page.id_segment())
        return '--'.join(parts)

    @cached_property
    def level(self) -> int:
        """
        The depth of the page's location within its :class:`.Volume`.

        Equals to number of parts in the :data:`id` plus 1.
        """
        level = len(self.path_in_volume.parts) + 1
        if self.path_in_volume.stem == '0' or self.path_in_volume.stem.startswith('0-'):
            level -= 1
        return level

    @property
    def antilevel(self) -> int:
        """
        A value that shows how far is this page's :data:`level` from the biggest level found in this :class:`.Volume`.

        For the pages with the biggest level, this value always equals to `1`.
        For other pages, it is always larger than `1`.

        :example: In a volume with only three pages, having levels `1`, `2`, `3`,
            their corresponding antilevels will be `3`, `2`, `1`.
        """
        return self.volume.max_level - self.level + 1

    # ------------------------------------------------------------------------------------------------------------------
    # Translation-related properties

    @property
    def original(self) -> Page:
        project = self.volume.project
        return project.get_translation(self, project.primary_language)

    @property
    def translation_status(self) -> TranslationStatus:
        this_version = self.meta.version
        orig_version = self.original.meta.version

        if this_version == orig_version:
            return TranslationStatus.UPTODATE
        if this_version.major == orig_version.major:
            return TranslationStatus.MODIFIED
        return TranslationStatus.OUTDATED


def _hash(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return sha256(data).hexdigest()


@dataclass(kw_only=True)
class PageMeta:
    version: Version = None

    def __post_init__(self):
        if self.version is not None:
            if not isinstance(self.version, Version):
                self.version = Version.parse(str(self.version))
