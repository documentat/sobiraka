from functools import cache

from .page import Page


class EmptyPage(Page):

    @property
    def syntax(self) -> str:
        return 'markdown'

    @cache
    def raw(self) -> str:
        return '# ' + self.path.stem + '\n\n{{ toc.local.md() }}'