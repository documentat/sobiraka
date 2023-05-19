from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from itertools import chain
from os.path import relpath
from textwrap import dedent
from typing import Awaitable, TYPE_CHECKING

from sobiraka.utils import render

if TYPE_CHECKING:
    from sobiraka.models import Page, Syntax, Volume
    from sobiraka.processing.abstract import Processor


class TableOfContents(metaclass=ABCMeta):
    @abstractmethod
    async def items(self) -> list[TocTreeItem]:
        ...


class CrossPageToc(TableOfContents, metaclass=ABCMeta):
    @abstractmethod
    def get_roots(self) -> tuple[Page, ...]:
        ...

    @abstractmethod
    async def get_title(self, page: Page) -> str:
        ...

    @abstractmethod
    def get_href(self, page: Page) -> str:
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

    async def items(self, *, skip_root: bool = True) -> list[TocTreeItem]:
        items = await self._make_items(self.get_roots())
        if skip_root:
            items = list(chain(*(root_item.children for root_item in items)))
        return items

    async def _make_items(self, pages: tuple[Page, ...]) -> list[TocTreeItem]:
        items: list[TocTreeItem] = []
        for page in pages:
            title = await self.get_title(page)
            href = self.get_href(page)
            is_current = self.is_current(page)
            is_selected = self.is_selected(page)
            children = await self._make_items(page.children)
            items.append(TocTreeItem(title, href, is_current=is_current, is_selected=is_selected, children=children))
        return items

    async def __call__(self) -> str:
        from .syntax import Syntax

        match self.syntax():
            case Syntax.HTML:
                return await self._render_html()
            case Syntax.MD:
                return await self._render_plaintext('{indent}- [{title}]({path})')
            case Syntax.RST:
                return await self._render_plaintext('{indent}- :doc:`{title} <{path}>`')

    async def _render_plaintext(self, line_template: str) -> str:
        text = ''
        for root in self.get_roots():
            for page in (root, *root.children_recursive):
                text += line_template.format(
                    indent="  " * page.level,
                    title=await self.get_title(page),
                    path=self.get_href(page))
                text += '\n'
        text = dedent(text)
        return text

    async def _render_html(self) -> str:
        template = '''
            <ul>
                {% for item in toc.items() recursive %}
                    <li>
                        {% if item.is_current %}
                            <strong>{{ item.title }}</strong>
                        {% else %}
                            <a href="{{ item.href }}">{{ item.title }}</a>
                        {% endif %}
                        {% if item.children %}
                            <ul>
                                {{ loop(item.children) }}
                            </ul>
                        {% endif %}
                    </li>
                {% endfor %}
            </ul>
            '''
        html = await render(template, toc=self)
        return html


@dataclass(eq=True)
class TocTreeItem:
    title: str
    href: str
    is_current: bool = field(kw_only=True, default=False)
    is_selected: bool = field(kw_only=True, default=False)
    children: list[TocTreeItem] = field(kw_only=True, default_factory=list)

    def __repr__(self):
        parts = [repr(self.title), repr(self.href)]
        if self.is_current:
            parts.append('current')
        if self.is_selected:
            parts.append('selected')
        if self.children:
            if len(self.children) == 1:
                parts.append('1 child item')
            else:
                parts.append(f'{len(self.children)} child items')
        return f'<{self.__class__.__name__}: ({", ".join(parts)}>'


@dataclass
class GlobalToc(CrossPageToc, metaclass=ABCMeta):
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


@dataclass
class SubtreeToc(CrossPageToc):
    processor: Processor
    current: Page | None

    def get_roots(self) -> tuple[Page, ...]:
        return self.current.children

    def get_title(self, page: Page) -> Awaitable[str]:
        return self.processor.get_title(page)

    def get_href(self, page: Page) -> str:
        return relpath(page.path_in_volume, start=self.current.path_in_volume.parent)

    def is_current(self, page: Page) -> bool:
        return False

    def is_selected(self, page: Page) -> bool:
        return False

    def syntax(self) -> Syntax:
        return self.current.syntax
