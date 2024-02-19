from __future__ import annotations

from dataclasses import dataclass, field
from textwrap import dedent, indent
from typing import Iterable, TYPE_CHECKING

import jinja2

from sobiraka.models.config import CombinedToc, Config
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

    title: str
    """The human-readable title of the item."""

    url: str
    """The link, most likely a relative URL of the target page."""

    number: TocNumber | None = field(kw_only=True, default=Unnumbered())
    """The item's number. If `None`, then the number must not be displayed."""

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


class Toc(list[TocItem]):
    """
    A list of Table Of Contents items, either top-level or any other level.
    Support both iterating and direct rendering (as an HTML list).

    It is very unlikely that you want to create a `Toc` object directly.
    Use `toc()` or `local_toc()` instead.
    """

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


def toc(
        base: Volume | Page,
        *,
        processor: Processor,
        current_page: Page | None = None,
        toc_expansion: int = None,
        combined_toc: CombinedToc = None,
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

    The `toc_expansion` limits the depth of the TOC.
    If it is 1, the items will only include one level of pages.
    If it is 2 and more, the TOC will include child pages.
    If a page has children but they would exceed the `toc_expansion` limit, its item is marked as `is_collapsed`.

    Note that in the current implementation, `toc_expansion` only applies to `Page`-based sub-items,
    while `Anchor`-based sub-items will be generated on any level according to the `combined_toc` argument.

    The `combined_toc` argument indicates whether to include local TOCs as subtrees of the TOC items.
    You may choose to always include them, never include them, or only include the current page's local TOC.

    If not set explicitly, `toc_expansion` and `combined_toc` will use the values from the volume's `Config_HTML`.
    """
    from sobiraka.models.page import Page
    from sobiraka.models.volume import Volume

    tree = Toc()

    volume: Volume
    config: Config
    pages: Iterable[Page]

    match base:
        case Volume():
            volume = base
            config = volume.config
            pages = volume.root_page.children
        case Page():
            volume = base.volume
            config = volume.config
            pages = base.children
        case _:
            raise TypeError(base)

    if toc_expansion is None:
        toc_expansion = config.html.toc_expansion
    if combined_toc is None:
        combined_toc = config.html.combined_toc

    for page in pages:
        item = TocItem(title=RT[page].title,
                       number=RT[page].number,
                       url=processor.make_internal_url(PageHref(page), page=current_page),
                       is_current=page is current_page,
                       is_selected=current_page is not None and page in current_page.breadcrumbs)

        if combined_toc is CombinedToc.ALWAYS or (combined_toc is CombinedToc.CURRENT and item.is_current):
            item.children += local_toc(page, href_prefix='' if item.is_current else item.url)

        if len(page.children) > 0:
            if toc_expansion > 1 or item.is_selected:
                item.children += toc(page,
                                     processor=processor,
                                     current_page=current_page,
                                     toc_expansion=toc_expansion - 1,
                                     combined_toc=combined_toc)
            else:
                item.is_collapsed = True

        tree.append(item)

    return tree


def local_toc(page: Page, *, href_prefix: str = '') -> Toc:
    """
    Generate a page's local toc, based on the information about anchors collected in `RT`.

    When called from within `toc()`, it is given a `href_prefix` which is prepended to each URL,
    thus creating a full URL that will lead a user to a specific section of a specific page.
    """
    breadcrumbs: list[Toc] = [Toc()]
    current_level: int = 0

    for anchor in RT[page].anchors:
        item = TocItem(title=anchor.label,
                       url=f'{href_prefix}#{anchor.identifier}',
                       number=RT[anchor].number)

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
