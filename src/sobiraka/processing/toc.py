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
    from sobiraka.models import Page
    from sobiraka.processing.abstract import Builder


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

    href: PageHref = field(kw_only=True, compare=False, default=None)

    origin: Page | Anchor = field(kw_only=True, compare=False, default=None)
    """The source from which the item was generated."""

    is_current: bool = field(kw_only=True, default=False)
    """True if the item corresponds to the currently opened page."""

    is_breadcrumb: bool = field(kw_only=True, default=False)
    """True if the item corresponds to the currently opened page or any of its parent pages."""

    children: Toc | CollapsedToc = field(kw_only=True, default_factory=list)
    """List of this item's sub-items."""

    def __repr__(self):
        parts: list[str] = [
            repr(self.number.format('{}. ') + self.title),
            repr(self.url),
        ]

        if self.is_current:
            parts.append('current')

        if self.is_breadcrumb:
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

    @property
    def is_collapsed(self) -> bool:
        """True if the item would have some children but they were omitted due to a depth limit."""
        return isinstance(self.children, CollapsedToc)


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
            if isinstance(item.origin, Anchor):
                if item.origin.header is header:
                    return item
        raise KeyError(header)


class CollapsedToc(tuple):
    """A value that indicates that some items would be here but were collapsed due to a depth limit."""


def toc(
        base: Page,
        *,
        builder: Builder,
        toc_depth: int | float = inf,
        combined_toc: CombinedToc = CombinedToc.NEVER,
        current_page: Page | None = None,
) -> Toc:
    """
    Generate a Table Of Contents.
    This function must be called after the `do_process3()` has been done for the volume,
    otherwise the TOC may end up missing anchors, numeration, etc.

    The TOC will contain items based on the given `base`.
    If given a `Volume`, the function will generate a top-level TOC.
    If given a `Page`, the function will generate a TOC of the page's child pages.

    The function uses `builder` and `current_page` for generating each item's correct URL.
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
    tree = Toc()

    if combined_toc is CombinedToc.ALWAYS or (combined_toc is CombinedToc.CURRENT and base is current_page):
        tree += local_toc(base,
                          builder=builder,
                          toc_depth=toc_depth,
                          current_page=current_page)

    for page in base.children:
        item_title = page.meta.toc_title or page.meta.title or page.location.name or page.volume.codename or ''
        href = PageHref(page)
        url = builder.make_internal_url(href, page=current_page)
        item = TocItem(title=item_title, url=url, href=href, origin=page,
                       number=RT[page].number, is_current=page is current_page)

        if current_page is not None:
            if page in current_page.breadcrumbs:
                item.is_breadcrumb = True

        if len(RT[page].anchors) > 0 or len(page.children) > 0:
            if (toc_depth > 1 and not page.meta.toc_collapse) or item.is_breadcrumb:
                item.children = toc(page,
                                    builder=builder,
                                    current_page=current_page,
                                    toc_depth=toc_depth - 1,
                                    combined_toc=combined_toc)
            else:
                item.children = CollapsedToc()

        tree.append(item)

    return tree


def local_toc(
        page: Page,
        *,
        builder: Builder,
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

        href = PageHref(page, anchor.identifier)
        url = builder.make_internal_url(href, page=current_page)
        item = TocItem(anchor.label, url, href=href, origin=anchor, number=RT[anchor].number)

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
