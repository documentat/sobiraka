from __future__ import annotations

from dataclasses import dataclass, field
from math import inf
from textwrap import dedent, indent
from typing import Iterable, TYPE_CHECKING

import jinja2
from panflute import Header

from sobiraka.models import Anchor
from sobiraka.models.config import CombinedToc
from sobiraka.models.href import PageHref
from sobiraka.runtime import RT
from sobiraka.utils import TocNumber, Unnumbered

if TYPE_CHECKING:
    from sobiraka.models import Page, Volume
    from sobiraka.processing.abstract import Processor


@dataclass
class TocItem:
    """
    A single item of a Table Of Contents. May include another `Toc`.

    A `TocItem` is self-contained: it does not reference any `Page` or other objects.
    Both the `title` and the `url` are pre-baked strings.
    The API is semi-stable, because custom themes in different projects use it directly.

    It is very unlikely that you want to create a `TocItem` object directly.
    Use `toc()` or `local_toc()` instead.
    """
    # pylint: disable=too-many-instance-attributes

    title: str
    """The human-readable title of the item."""

    url: str
    """The link, most likely a relative URL of the target page."""

    number: TocNumber = field(kw_only=True, default=Unnumbered())
    """The item's number. If `None`, then the number must not be displayed."""

    source: Page | Anchor = field(compare=False, default=None)
    """The source from which the item was generated."""

    is_current: bool = field(kw_only=True, default=False)
    """True if the item corresponds to the currently opened page."""

    is_selected: bool = field(kw_only=True, default=False)
    """True if the item corresponds to the currently opened page or any of its parent pages."""

    is_collapsed: bool = field(kw_only=True, default=False)
    """True if the item would have some children but they were omitted due to a depth limit."""

    children: Toc = field(kw_only=True, default_factory=list)
    """List of this item's sub-items."""

    def __repr__(self):
        parts: list[str] = [
            repr(self.number.format('{}. ') + self.title),
            repr(self.url),
        ]

        if self.is_current:
            parts.append('current')

        if self.is_selected:
            parts.append('selected')

        if self.is_collapsed:
            parts.append('collapsed')

        if self.children:
            part_children = '[\n'
            for child in self.children:
                part_children += indent(repr(child), '  ') + ',\n'
            part_children += ']'
            parts.append(part_children)

        return f'<{self.__class__.__name__}: {", ".join(parts)}>'

    def walk(self) -> Iterable[TocItem]:
        for subitem in self.children:
            yield subitem
            yield from subitem.walk()


class Toc(list[TocItem]):
    """
    A list of Table Of Contents items, either top-level or any other level.
    Support both iterating and direct rendering (as an HTML list).

    It is very unlikely that you want to create a `Toc` object directly.
    Use `toc()` or `local_toc()` instead.
    """

    def __init__(self, *items: TocItem):
        super().__init__(items)

    def __str__(self):
        jinja = jinja2.Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,
        )
        template = jinja.from_string(dedent('''
            <ul>
              {% for item in toc recursive %}
                <li>
                  {% if item.is_current %}
                    <strong>{{ item.title }}</strong>
                  {% else %}
                    <a href="{{ item.url }}">{{ item.title }}</a>
                  {% endif %}
                  {% if item.children %}
                    <ul>
                      {{ loop(item.children) | indent(10) }}
                    </ul>
                  {% endif %}
                </li>
              {% endfor %}
            </ul>
            '''.rstrip()))
        return template.render(toc=self)

    def walk(self) -> Iterable[TocItem]:
        for item in self:
            yield item
            yield from item.walk()

    def find_item_by_header(self, header: Header) -> TocItem:
        for item in self.walk():
            if isinstance(item.source, Anchor):
                if item.source.header is header:
                    return item
        raise KeyError(header)


def toc(
        base: Volume | Page,
        *,
        processor: Processor,
        toc_depth: int | float,
        combined_toc: CombinedToc,
        current_page: Page | None = None,
) -> Toc:
    """
    Generate a Table Of Contents.
    This function must be called after the `process3()` has been done for the volume,
    otherwise the TOC may end up missing anchors, numeration, etc.

    The TOC will contain items based on the given `base`.
    If given a `Volume`, the function will generate a top-level TOC.
    If given a `Page`, the function will generate a TOC of the page's child pages.

    The function uses `processor` and `current_page` for generating each item's correct URL.
    Also, the `current_page` is used for marking `TocItem`s as current or selected.

    The `toc_depth` limits the depth of the TOC.
    If it is 1, the items will only include one level of pages.
    If it is 2 and more, the TOC will include child pages.
    If a page has children but they would exceed the `toc_depth` limit, its item is marked as `is_collapsed`.

    Note that in the current implementation, `toc_depth` only applies to `Page`-based sub-items,
    while `Anchor`-based sub-items will be generated on any level according to the `combined_toc` argument.

    The `combined_toc` argument indicates whether to include local TOCs as subtrees of the TOC items.
    You may choose to always include them, never include them, or only include the current page's local TOC.
    """
    from sobiraka.models.page import Page
    from sobiraka.models.volume import Volume

    pages: Iterable[Page]
    match base:
        case Volume():
            pages = base.root_page.children
        case Page():
            pages = base.children
        case _:
            raise TypeError(base)

    tree = Toc()

    for page in pages:
        item = TocItem(title=RT[page].title,
                       url=processor.make_internal_url(PageHref(page), page=current_page),
                       number=RT[page].number,
                       source=page,
                       is_current=page is current_page,
                       is_selected=current_page is not None and page in current_page.breadcrumbs)

        if combined_toc is CombinedToc.ALWAYS or (combined_toc is CombinedToc.CURRENT and item.is_current):
            item.children += local_toc(page,
                                       processor=processor,
                                       toc_depth=toc_depth - 1,
                                       current_page=current_page)

        if len(page.children) > 0:
            if toc_depth > 1 or item.is_selected:
                item.children += toc(page,
                                     processor=processor,
                                     current_page=current_page,
                                     toc_depth=toc_depth - 1,
                                     combined_toc=combined_toc)
            else:
                item.is_collapsed = True

        tree.append(item)

    return tree


def local_toc(
        page: Page,
        *,
        processor: Processor,
        toc_depth: int | float = inf,
        current_page: Page | None = None,
) -> Toc:
    """
    Generate a page's local toc, based on the information about anchors collected in `RT`.

    When called from within `toc()`, it is given a `href_prefix` which is prepended to each URL,
    thus creating a full URL that will lead a user to a specific section of a specific page.
    """
    breadcrumbs: list[Toc] = [Toc()]
    current_level: int = 0

    for anchor in RT[page].anchors:
        if anchor.level > toc_depth + 1:
            continue

        url = processor.make_internal_url(PageHref(page, anchor.identifier), page=current_page)
        item = TocItem(title=anchor.label, url=url, number=RT[anchor].number, source=anchor)

        if anchor.level == current_level:
            breadcrumbs[-2].append(item)
            breadcrumbs[-1] = item.children
        elif anchor.level > current_level:
            breadcrumbs[-1].append(item)
            breadcrumbs.append(item.children)
        elif anchor.level < current_level:
            breadcrumbs[anchor.level - 2].append(item)
            breadcrumbs[anchor.level - 1:] = [item.children]
        current_level = anchor.level

    return breadcrumbs[0]
