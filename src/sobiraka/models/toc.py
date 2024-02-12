from __future__ import annotations

from dataclasses import dataclass, field
from textwrap import dedent, indent
from typing import Iterable, TYPE_CHECKING

import jinja2
from sobiraka.models.config import Config
from sobiraka.runtime import RT
from sobiraka.utils import TocNumber

from .config import CombinedToc
from .href import PageHref

if TYPE_CHECKING:
    from sobiraka.models import Page, Volume
    from sobiraka.processing.abstract import Processor


@dataclass
class TocItem:
    title: str
    url: str
    number: TocNumber = field(kw_only=True, default=None)
    is_current: bool = field(kw_only=True, default=False)
    is_selected: bool = field(kw_only=True, default=False)
    is_collapsed: bool = field(kw_only=True, default=False)
    children: Toc = field(kw_only=True, default_factory=list)

    def __repr__(self):
        parts = [repr(self.title), repr(self.url)]

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
    from .page import Page
    from .volume import Volume

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
