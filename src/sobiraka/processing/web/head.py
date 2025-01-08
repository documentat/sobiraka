from abc import ABCMeta, abstractmethod
from dataclasses import dataclass

from sobiraka.utils import RelativePath


class HeadTag(metaclass=ABCMeta):
    @abstractmethod
    def render(self, root_prefix: str) -> str:
        ...


class Head(list[HeadTag]):
    def append(self, tag: HeadTag):
        if tag not in self:
            super().append(tag)

    def render(self, root_prefix: str) -> str:
        head = ''
        for tag in self:
            head += tag.render(root_prefix) + '\n'
        return head


# ------------------------------------------------------------------------------
# CSS


@dataclass(frozen=True)
class HeadCssCode(HeadTag):
    code: str

    def render(self, root_prefix: str) -> str:
        code = self.code.replace('%ROOT%', root_prefix)
        return f'<style>\n{code}\n</style>'


@dataclass(frozen=True)
class HeadCssFile(HeadTag):
    path: RelativePath

    def render(self, root_prefix: str) -> str:
        return f'<link rel="stylesheet" href="{root_prefix}{self.path}"/>'


@dataclass(frozen=True)
class HeadCssUrl(HeadTag):
    url: str

    def render(self, root_prefix: str) -> str:
        return f'<link rel="stylesheet" href="{self.url}"/>'


# ------------------------------------------------------------------------------
# JavaScript


@dataclass(frozen=True)
class HeadJsCode(HeadTag):
    code: str

    def render(self, root_prefix: str) -> str:
        code = self.code.replace('%ROOT%', root_prefix)
        return f'<script>\n{code}\n</script>'


@dataclass(frozen=True)
class HeadJsFile(HeadTag):
    path: RelativePath

    def render(self, root_prefix: str) -> str:
        return f'<script src="{root_prefix}{self.path}"></script>'


@dataclass(frozen=True)
class HeadJsUrl(HeadTag):
    url: str

    def render(self, root_prefix: str) -> str:
        return f'<script src="{self.url}"></script>'
