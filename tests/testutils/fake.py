from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sobiraka.models import Page, Volume, Syntax


@dataclass(kw_only=True, frozen=True)
class FakeVolume(Volume):
    syntax: Syntax = Syntax.MD
    fake_files: tuple[str, ...] = ()

    def _find_files(self) -> set[Path]:
        return set(self.root / file for file in self.fake_files)

    def _init_page(self, path: Path) -> FakePage:
        return FakePage(self, path)


class FakePage(Page):
    def raw(self) -> str:
        title = self.id_segment()
        match self.syntax:
            case Syntax.MD:
                return f'#{title}\n'
            case Syntax.RST:
                return f'{title}\n{"-" * len(title)}\n'
