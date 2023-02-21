import re
from functools import cache

from .page import Page


class EmptyPage(Page):

    def _id_segment(self) -> str:
        if self.parent is None:
            return 'r'
        else:
            return re.sub(r'^(\d+-)?', '', self.relative_path.stem)

    @property
    def is_index(self) -> bool:
        return True

    @property
    def syntax(self) -> str:
        return 'markdown-smart'

    @cache
    def raw(self) -> str:
        return '# ' + self.path.stem + '\n\n{{ toc.local.md() }}'