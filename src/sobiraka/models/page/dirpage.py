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
        return self.volume.pages_by_path[self.path_in_volume.parent]

    @property
    def syntax(self) -> Syntax:
        return Syntax.MD

    # pylint: disable=method-cache-max-size-none
    @property
    def text(self) -> str:
        return '# ' + self.path_in_volume.stem + '\n\n{{ toc }}'
