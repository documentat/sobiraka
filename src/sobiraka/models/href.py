from __future__ import annotations

import re
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

if typing.TYPE_CHECKING: from .page import Page


class Href(ABC):
    @abstractmethod
    def __str__(self): ...


@dataclass(frozen=True)
class UrlHref(Href):
    url: str

    def __str__(self):
        return self.url

    def __repr__(self):
        return f'{self.__class__.__name__}({self.url!r})'


@dataclass(frozen=True)
class PageHref(Href):
    target: Page
    anchor: str | None = None

    def __str__(self):
        text = ''
        if self.target:
            text += str(self.target.relative_path)
        if self.anchor:
            text += '#' + self.anchor
        return text

    def __repr__(self):
        text = self.__class__.__name__ + '('
        text += repr(self.target)
        if self.anchor:
            text += ', ' + repr(self.anchor)
        text += ')'
        return text


@dataclass(frozen=True)
class UnknownPageHref(Href):
    target: str
    anchor: str | None = None

    def __str__(self):
        text = self.target
        if self.anchor:
            text += '#' + self.anchor
        return text

    def __repr__(self):
        text = self.__class__.__name__ + '('
        text += repr(self.target)
        if self.anchor:
            text += ', ' + repr(self.anchor)
        text += ')'
        return text