from pathlib import Path

from .page import Page


class IndexPage(Page):

    @property
    def index(self) -> int | float:
        return self.volume.config.paths.naming_scheme.get_index(self.path_in_project.parent)

    @property
    def stem(self) -> str:
        return self.volume.config.paths.naming_scheme.get_stem(self.path_in_project.parent)

    def is_root(self) -> bool:
        return self.path_in_volume.parent == Path('.')

    @property
    def parent(self) -> Page | None:
        if self.is_root():
            return None
        return self.volume.pages_by_path[self.path_in_volume.parent.parent]

    @property
    def hash(self) -> str:
        return '2222222222222222222222222222222222222222222222222222222222222222'
