from __future__ import annotations

import os
from contextvars import ContextVar, copy_context
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Awaitable, Callable

from panflute import Doc, Image, Link
from sobiraka.models import Anchors, Href, Issue, Page
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

    converted_image_urls: list[tuple[Image, str]] = field(default_factory=list)
    links_that_follow_images: list[tuple[Image, Link]] = field(default_factory=list)
