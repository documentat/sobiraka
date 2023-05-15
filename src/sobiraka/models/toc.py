from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Awaitable, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from sobiraka.models import Page, Syntax, Volume
    from sobiraka.processing.abstract import Processor


class TableOfContents(metaclass=ABCMeta):
    @abstractmethod
    def get_roots(self) -> tuple[Page, ...]:
        ...

    @abstractmethod
    async def get_title(self, page: Page) -> str:
        ...

    @abstractmethod
    def get_href(self, page: Page) -> Path:
        ...

    @abstractmethod
    def is_current(self, page: Page) -> bool:
        ...

    @abstractmethod
    def is_selected(self, page: Page) -> bool:
        ...

    @abstractmethod
    def syntax(self) -> Syntax:
        ...

    async def __call__(self) -> str:
        from .syntax import Syntax

        line_template = {
            Syntax.MD: '{indent}- [{title}](/{path})',
            Syntax.RST: '{indent}- :doc:`{title} </{path}>`',
        }[self.syntax()]

        text = ''
        for root in self.get_roots():
            for page in (root, *root.children_recursive):
                text += line_template.format(
                    indent="  " * page.level,
                    title=await self.get_title(page),
                    path=page.path_in_volume)
                text += '\n'
        text = dedent(text)
        return text

    async def __aiter__(self) -> Iterable[TocTreeItem]:
        async def items(pages: tuple[Page, ...]) -> tuple[TocTreeItem, ...]:
            _items: list[TocTreeItem] = []
            for _page in pages:
                _children = await items(_page.children)
                _items.append(
                    TocTreeItem(
                        title=await self.get_title(_page),
                        href=self.get_href(_page),
                        is_current=self.is_current(_page),
                        is_selected=self.is_selected(_page),
                        children=_children))
            return tuple(_items)

        for root_item in await items(self.get_roots()):
            yield root_item


@dataclass(kw_only=True, frozen=True)
class TocTreeItem:
    title: str
    href: Path
    is_current: bool = False
    is_selected: bool = False
    children: tuple[TocTreeItem, ...] = ()


@dataclass
class LocalToc(TableOfContents):
    processor: Processor
    current: Page | None

    def get_roots(self) -> tuple[Page, ...]:
        return self.current.children

    def get_title(self, page: Page) -> Awaitable[str]:
        return self.processor.get_title(page)

    def get_href(self, page: Page) -> Path:
        return Path('/') / page.path_in_volume

    def is_current(self, page: Page) -> bool:
        return False

    def is_selected(self, page: Page) -> bool:
        return False

    def syntax(self) -> Syntax:
        return self.current.syntax


@dataclass
class GlobalToc(TableOfContents, metaclass=ABCMeta):
    processor: Processor
    volume: Volume
    current: Page

    def get_roots(self) -> tuple[Page, ...]:
        return tuple(page for page in self.volume.pages if page.parent is None)

    def get_title(self, page: Page) -> Awaitable[str]:
        return self.processor.get_title(page)

    def is_current(self, page: Page) -> bool:
        return page is self.current

    def is_selected(self, page: Page) -> bool:
        return page in self.current.breadcrumbs

    def syntax(self) -> Syntax:
        raise NotImplementedError('Iterate through items manually')
