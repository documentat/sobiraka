from dataclasses import dataclass, field
from pathlib import Path

from sobiraka.models import IndexPage, Page, Syntax, Volume
from sobiraka.models.config import Config_Paths


@dataclass(kw_only=True, frozen=True)
class FakeVolume(Volume):
    paths: Config_Paths = field(default=Config_Paths(root=Path('/')))

    syntax: Syntax = Syntax.MD
    fake_files: tuple[str, ...] = ()

    def _find_files(self) -> set[Path]:
        return set(self.root / file for file in self.fake_files)

    def _init_page(self, path_in_project: Path) -> Page:
        return super()._init_page(path_in_project,
                                  page_class=FakePage,
                                  indexpage_class=FakeIndexPage)


@dataclass(frozen=True)
class FakePage(Page):
    _meta_text: str = field(kw_only=True, default='')

    def _raw(self) -> str:
        title = self.id_segment()
        match self.syntax:
            case Syntax.MD:
                raw = f'#{title}\n'
            case Syntax.RST:
                raw = f'{title}\n{"-" * len(title)}\n'
            case _:
                raise ValueError(self.syntax)

        if self._meta_text:
            raw = f'---\n{self._meta_text}\n---\n{raw}'

        return raw


class FakeIndexPage(FakePage, IndexPage):
    pass
