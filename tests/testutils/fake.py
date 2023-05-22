from dataclasses import dataclass
from pathlib import Path

from sobiraka.models import IndexPage, Page, Syntax, Volume


@dataclass(kw_only=True, frozen=True)
class FakeVolume(Volume):
    syntax: Syntax = Syntax.MD
    fake_files: tuple[str, ...] = ()

    def _find_files(self) -> set[Path]:
        return set(self.root / file for file in self.fake_files)

    def _init_page(self, path_in_project: Path) -> Page:
        return super()._init_page(path_in_project,
                                  page_class=FakePage,
                                  indexpage_class=FakeIndexPage)


class FakePage(Page):
    def raw(self) -> str:
        title = self.id_segment()
        match self.syntax:
            case Syntax.MD:
                return f'#{title}\n'
            case Syntax.RST:
                return f'{title}\n{"-" * len(title)}\n'


class FakeIndexPage(FakePage, IndexPage):
    pass
