from sobiraka.utils import RelativePath
from .page import Page


class IndexPage(Page):

    @property
    def pos(self) -> int | float:
        return self.volume.config.paths.naming_scheme.parse(self.path_in_project.parent).pos

    @property
    def stem(self) -> str:
        return self.volume.config.paths.naming_scheme.parse(self.path_in_project.parent).stem

    def is_root(self) -> bool:
        return self.path_in_volume.parent == RelativePath('.')

    @property
    def parent(self) -> Page | None:
        if self.is_root():
            return None
        return self.volume.pages_by_path[self.path_in_volume.parent.parent]

    @property
    def hash(self) -> str:
        return '2222222222222222222222222222222222222222222222222222222222222222'
