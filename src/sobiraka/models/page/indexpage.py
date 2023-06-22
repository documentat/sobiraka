import re
from pathlib import Path

from .page import Page


class IndexPage(Page):

    def id_segment(self) -> str:
        if self.is_root():
            return 'r'
        return re.sub(r'^(\d+-)?', '', self.path_in_project.parent.stem)

    def is_root(self) -> bool:
        return self.path_in_volume.parent == Path('.')

    @property
    def parent(self) -> Page | None:
        if self.is_root():
            return None
        return self.volume.pages_by_path[self.path_in_volume.parent.parent]
