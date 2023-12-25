from __future__ import annotations

import json
import os
from contextvars import ContextVar, copy_context
from dataclasses import asdict, dataclass, field
from importlib.resources import files
from io import StringIO
from pathlib import Path
from typing import Awaitable, Callable

import panflute.io
from panflute import Doc

from sobiraka.models import Anchor, Anchors, Href, Issue, Page, PageHref, UrlHref
from sobiraka.utils import TocNumber, UNNUMBERED, UniqueList


class Runtime:
    PAGES: ContextVar[dict[Page, PageRuntime]] = ContextVar('pages')

    def __init__(self):
        # pylint: disable=invalid-name
        self.FILES: Path = files('sobiraka') / 'files'
        self.TMP: Path | None = None
        self.DEBUG: bool = bool(os.environ.get('SOBIRAKA_DEBUG'))
        self.IDS: dict[int, str] = {}

    @classmethod
    async def run_isolated(cls, func: Callable[..., Awaitable]):
        async def wrapped_func():
            RT.PAGES.set({})
            return await func()

        ctx = copy_context()
        return await ctx.run(wrapped_func)

    def __getitem__(self, page: Page) -> PageRuntime:
        pages = self.PAGES.get()

        if page not in pages:
            pages[page] = PageRuntime()
        return pages[page]

    def __setitem__(self, page: Page, page_rt: PageRuntime):
        pages = self.PAGES.get()

        pages[page] = page_rt


RT = Runtime()


@dataclass
class PageRuntime:
    # pylint: disable=too-many-instance-attributes

    doc: Doc = None
    """
    The document tree, as parsed by `Pandoc <https://pandoc.org/>`_ 
    and `Panflute <http://scorreia.com/software/panflute/>`_.
    
    Do not rely on the value for page here until `load()` is awaited for that page.
    """

    title: str = None
    """Page title.
    
    Do not rely on the value for page here until `process1()` is awaited for that page.
    """

    number: TocNumber = UNNUMBERED
    """
    Number of the page global TOC.
    """

    links: list[Href] = field(default_factory=list)
    """All links present on the page, both internal and external.
    
    Do not rely on the value for page here until `process1()` is awaited for that page."""

    anchors: Anchors = field(default_factory=Anchors)
    """Dictionary containing anchors and corresponding readable titles.
    
    Do not rely on the value for page here until `process1()` is awaited for that page.
    
    Note that sometime a user leaves anchors empty or specifies identical anchors for multiple headers by mistake.
    However, this is not considered a critical issue as long as no page contains links to this anchor.
    For that reason, all the titles for an anchor are stored as a list (in order of appearance on the page),
    and it is up to `process2_link()` to report an issue if necessary.
    """

    issues: UniqueList[Issue] = field(default_factory=UniqueList)

    dependencies: set[Page] = field(default_factory=set)

    latex: bytes = None

    def dump(self) -> dict:
        data = {}

        data['doc'] = json.dumps(self.doc.to_json())

        data['title'] = self.title

        data['links'] = []
        for href in self.links:
            match href:
                case PageHref() as page_href:
                    data['links'].append({
                        'type': 'PageHref',
                        'target': str(page_href.target.path_in_volume),
                        'anchor': page_href.anchor,
                    })
                case UrlHref() as url_href:
                    data['links'].append({
                        'type': 'UrlHref',
                        'url': url_href.url,
                    })
                case _:
                    raise TypeError(type(href))

        data['anchors'] = list(map(asdict, self.anchors))

        data['issues'] = []
        for issue in self.issues:
            data['issues'].append((issue.__class__.__name__, asdict(issue)))

        data['dependencies'] = sorted(list(str(page.path_in_volume) for page in self.dependencies))

        return data

    @staticmethod
    def load(data: dict, page: Page) -> PageRuntime:
        volume = page.volume

        if 'doc' in data:
            data['doc'] = panflute.load(StringIO(data['doc']))

        if 'links' in data:
            for i, href in enumerate(data['links']):
                match href:
                    case {'type': 'PageHref', 'target': str() as target, 'anchor': str() | None as anchor}:
                        target = volume.pages_by_path[target]
                        data['links'][i] = PageHref(target, anchor)
                    case {'type': 'UrlHref', 'url': str() as url}:
                        data['links'][i] = UrlHref(url)

        if 'anchors' in data:
            data['anchors'] = Anchors(Anchor(**anchor_data) for anchor_data in data['anchors'])

        if 'issues' in data:
            from sobiraka.models import issue
            for issue_class_name, issue_data in data['issues']:
                issue_class = getattr(issue, issue_class_name)
                data['issues'].append(issue_class(**issue_data))

        if 'dependencies' in data:
            data['dependencies'] = set(volume.pages_by_path[Path(dep_path)] for dep_path in data['dependencies'])

        return PageRuntime(**data)
