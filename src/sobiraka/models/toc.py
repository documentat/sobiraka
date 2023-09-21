from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from os.path import relpath
from typing import TYPE_CHECKING

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
    def get_root(self) -> Page:
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

    async def items(self, *, parent: Page = None) -> list[TocTreeItem]:
        if parent is None:
            parent = self.get_root()
        items: list[TocTreeItem] = []
        for page in parent.children:
            items.append(await self._make_item(page))
            items[-1].children = await self.items(parent=page)
        return items

    async def _make_item(self, page: Page) -> TocTreeItem:
        title = await self.get_title(page)
        href = self.get_href(page)
        is_current = self.is_current(page)
        is_selected = self.is_selected(page)
        return TocTreeItem(title, href, is_current=is_current, is_selected=is_selected)

    async def __call__(self) -> str:
        from .syntax import Syntax

        match self.syntax():
            case Syntax.HTML:
                return await self._render_html()
            case Syntax.MD:
                return await self._render_plaintext('{indent}- [{title}]({path})')
            case Syntax.RST:
                return await self._render_plaintext('{indent}- :doc:`{title} <{path}>`')

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

    async def _render_plaintext(self, line_template: str, level: int = 0, items: list[TocTreeItem] = None) -> str:
        if items is None:
            items = await self.items()
        text = ''
        for item in items:
            text += line_template.format(
                indent="  " * level,
                title=item.title,
                path=item.href)
            text += '\n'
            text += await self._render_plaintext(line_template, level + 1, item.children)
        return text


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
        return f'<{self.__class__.__name__}: {", ".join(parts)}>'


@dataclass
class GlobalToc(CrossPageToc, metaclass=ABCMeta):
    processor: Processor
    volume: Volume
    current: Page

    def get_root(self) -> Page:
        return self.volume.root_page

    async def get_title(self, page: Page) -> str:
        return await self.processor.get_title(page)

    def is_current(self, page: Page) -> bool:
        return page is self.current

    def is_selected(self, page: Page) -> bool:
        return page in self.current.breadcrumbs


@dataclass
class SubtreeToc(CrossPageToc):
    processor: Processor
    current: Page | None

    def get_root(self) -> Page:
        return self.current

    async def get_title(self, page: Page) -> str:
        return await self.processor.get_title(page)

    def get_href(self, page: Page) -> str:
        return relpath(page.path_in_volume, start=self.current.path_in_volume.parent)

    def is_current(self, page: Page) -> bool:
        return False

    def is_selected(self, page: Page) -> bool:
        return False

    def syntax(self) -> Syntax:
        return self.current.syntax


@dataclass
class LocalToc(TableOfContents):
    processor: Processor
    page: Page

    async def items(self) -> list[TocTreeItem]:
        root = TocTreeItem(title='', href='')
        breadcrumbs: list[TocTreeItem] = [root]
        current_level: int = 0

        for anchor in self.processor.anchors[self.page]:
            item = TocTreeItem(title=anchor.label, href=f'#{anchor.identifier}')
            if anchor.header.level == current_level:
                breadcrumbs[-2].children.append(item)
                breadcrumbs[-1] = item
            elif anchor.header.level > current_level:
                breadcrumbs[-1].children.append(item)
                breadcrumbs.append(item)
            elif anchor.header.level < current_level:
                breadcrumbs[anchor.header.level - 1].children.append(item)
                breadcrumbs[anchor.header.level:] = [item]
            current_level = anchor.header.level

        # TODO: Support sources with zero or multiple top-level headers
        if root.children:
            assert len(root.children) == 1, str(root.children)
            root.children = root.children[0].children

        return root.children
