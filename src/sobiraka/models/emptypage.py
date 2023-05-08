import re
from functools import cache
from pathlib import Path

from .page import Page


class EmptyPage(Page):

    def _id_segment(self) -> str:
        if self.parent is None:
            return 'r'
        else:
            return re.sub(r'^(\d+-)?', '', self.path.stem)

    def is_index(self) -> bool:
        return True

    @property
    def path_in_project(self) -> Path:
        return self.path.relative_to(self.volume.project.base)

    @property
    def path_in_volume(self) -> Path:
        return self.path.relative_to(self.volume.root)

    @property
    def parent(self) -> Page | None:
        return self.volume.pages_by_path.get(self.path_in_project.parent)

    @property
    def syntax(self) -> str:
        return 'markdown-smart'

    @cache
    def raw(self) -> str:
        return '# ' + self.path.stem + '\n\n{{ toc.local.md() }}'