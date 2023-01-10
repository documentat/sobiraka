from __future__ import annotations

import re
from asyncio import create_task, Task
from functools import cached_property
from pathlib import Path
from typing import Awaitable, Callable, Coroutine

from panflute import Doc

from . import Href
from .book import Book
from .error import ProcessingError


class Page:
    def __init__(self, book: Book, path: Path):
        self.book: Book = book
        self.path: Path = path

        self.doc: Doc | None = None
        self.title: str | None = None
        self.links: list[Href] = []
        self.anchors: dict[str, list[str]] = {}
        self.latex: bytes | None = None

        self.errors: set[ProcessingError] = set()

        self.process2_tasks: list[Awaitable] = []

        from ..building.loading import load_page
        from ..building.processing1 import process1
        from ..building.processing2 import process2
        from ..building.rendering import generate_latex
        self.loaded = _TriggerableAction(lambda: load_page(self))
        self.processed1 = _TriggerableAction(lambda: process1(self))
        self.processed2 = _TriggerableAction(lambda: process2(self))
        self.latex_generated = _TriggerableAction(lambda: generate_latex(self))

    def __repr__(self):
        return f'<Page: {str(self.relative_path)!r}>'

    @cached_property
    def relative_path(self) -> Path:
        return self.path.relative_to(self.book.root)

    @cached_property
    def id(self) -> str:
        parts = list(self.relative_path.with_suffix('').parts)
        if parts[-1] == '0' or parts[-1].startswith('0-'):
            parts = parts[:-1]
        for i, part in enumerate(parts):
            parts[i] = re.sub(r'^(\d+-)?', '', part)
        return '--'.join(parts)

    @cached_property
    def level(self) -> int:
        level = len(self.relative_path.parts)
        if self.path.stem == '0' or self.path.stem.startswith('0-'):
            level -= 1
        return level

    @property
    def antilevel(self) -> int:
        return self.book.max_level - self.level + 1


class _TriggerableAction:
    def __init__(self, action: Callable[[], Coroutine]):
        self.action: Callable[[], Coroutine] = action
        self.task: Task | None = None

    def start(self):
        if self.task is None:
            self.task = create_task(self.action())

    async def wait(self):
        self.start()
        await self.task