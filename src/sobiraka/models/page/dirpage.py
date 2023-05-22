from functools import cache
from pathlib import Path

from .page import Page
from ..syntax import Syntax


class DirPage(Page):

    def is_root(self) -> bool:
        return self.path_in_volume == Path('.')

    @property
    def parent(self) -> Page | None:
        if self.is_root():
            return None
        return self.volume.pages_by_path[self.path_in_project.parent]

    @property
    def path_in_project(self) -> Path:
        return self.path.relative_to(self.volume.project.base)

    @property
    def path_in_volume(self) -> Path:
        return self.path.relative_to(self.volume.root)

    @property
    def syntax(self) -> Syntax:
        return Syntax.MD

    # pylint: disable=method-cache-max-size-none
    @cache
    def raw(self) -> str:
        return '# ' + self.path.stem + '\n\n{{ toc.md }}'
