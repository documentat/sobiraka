from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

if typing.TYPE_CHECKING:
    from .page import Page


class Href(ABC):
    @abstractmethod
    def __str__(self):
        ...

    def __lt__(self, other):
        if isinstance(self, UrlHref) and isinstance(other, PageHref):
            return True
        if isinstance(self, PageHref) and isinstance(other, UrlHref):
            return False
        if type(self) is type(other):
            self_values = tuple(v or '' for v in self.__dict__.values())
            other_values = tuple(v or '' for v in other.__dict__.values())
            return self_values < other_values
        raise ValueError((self, other))


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
    anchor: str = None
    default_label: str = field(default=None, kw_only=True, compare=False)

    def __str__(self):
        text = ''
        if self.target:
            text += str(self.target.location)
        if self.anchor:
            text += '#' + self.anchor
        return text

    def __repr__(self):
        text = self.__class__.__name__ + '('
        text += repr(self.target)
        if self.anchor:
            text += ', ' + repr(self.anchor)
        if self.default_label:
            text += ', default_label=' + repr(self.default_label)
        text += ')'
        return text

    def url_relative_to(self, page: Page) -> str:
        url = str(self.target.source.path_in_project.relative_to(page.source.path_in_project.parent))
        if self.anchor:
            url += '#' + self.anchor
        return url
