from __future__ import annotations

import os
from collections import defaultdict
from contextvars import ContextVar, copy_context
from typing import Coroutine, TYPE_CHECKING, overload

from .anchorruntime import AnchorRuntime
from .pageruntime import PageRuntime
from ..utils import AbsolutePath

if TYPE_CHECKING:
    from sobiraka.models import Anchor, Page, Volume


class Runtime:
    ANCHORS: ContextVar[dict[Anchor, AnchorRuntime]] = ContextVar('anchors')
    PAGES: ContextVar[dict[Page, PageRuntime]] = ContextVar('pages')

    def __init__(self):
        # pylint: disable=invalid-name
        self.TMP: AbsolutePath | None = None
        self.DEBUG: bool = bool(os.environ.get('SOBIRAKA_DEBUG'))
        self.CLASSES: dict[int, str] = {}

    @classmethod
    def init_context_vars(cls):
        RT.PAGES.set(defaultdict(PageRuntime))
        RT.ANCHORS.set(defaultdict(AnchorRuntime))

    @classmethod
    async def run_isolated(cls, func: Coroutine):
        async def wrapped_func():
            cls.init_context_vars()
            return await func

        ctx = copy_context()
        return await ctx.run(wrapped_func)

    @overload
    def __getitem__(self, page: Anchor) -> AnchorRuntime:
        ...

    @overload
    def __getitem__(self, page: Page) -> PageRuntime:
        ...

    def __getitem__(self, key: Anchor | Page | Volume):
        from sobiraka.models import Anchor, Page
        match key:
            case Anchor() as anchor:
                return self.ANCHORS.get()[anchor]
            case Page() as page:
                return self.PAGES.get()[page]
            case _:
                raise KeyError(key)


RT = Runtime()
