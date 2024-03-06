from __future__ import annotations

import os
from collections import defaultdict
from contextvars import ContextVar, copy_context
from pathlib import Path
from typing import Coroutine, TYPE_CHECKING, overload

from .anchorruntime import AnchorRuntime
from .pageruntime import PageRuntime
from .volumeruntime import VolumeRuntime

if TYPE_CHECKING:
    from sobiraka.models import Anchor, Page, Volume


class Runtime:
    PAGES: ContextVar[dict[Page, PageRuntime]] = ContextVar('pages')
    VOLUMES: ContextVar[dict[Volume, VolumeRuntime]] = ContextVar('volumes')
    ANCHORS: ContextVar[dict[Anchor, AnchorRuntime]] = ContextVar('anchors')

    def __init__(self):
        # pylint: disable=invalid-name
        self.TMP: Path | None = None
        self.DEBUG: bool = bool(os.environ.get('SOBIRAKA_DEBUG'))
        self.IDS: dict[int, str] = {}

    @classmethod
    def init_context_vars(cls):
        RT.VOLUMES.set(defaultdict(VolumeRuntime))
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
    def __getitem__(self, volume: Volume) -> VolumeRuntime:
        ...

    @overload
    def __getitem__(self, page: Page) -> PageRuntime:
        ...

    @overload
    def __getitem__(self, page: Anchor) -> AnchorRuntime:
        ...

    def __getitem__(self, key: Anchor | Page | Volume):
        from sobiraka.models import Anchor, Page, Volume
        match key:
            case Anchor() as anchor:
                return self.ANCHORS.get()[anchor]
            case Page() as page:
                return self.PAGES.get()[page]
            case Volume() as volume:
                return self.PAGES.get()[volume]
            case _:
                raise KeyError(key)


RT = Runtime()
