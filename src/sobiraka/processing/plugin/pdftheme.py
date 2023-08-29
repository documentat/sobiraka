from abc import ABCMeta
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from .plugin import Plugin, load_plugin


@dataclass
class PdfTheme(Plugin, metaclass=ABCMeta):
    sty: Path = None
    cover: Path = None


def load_pdf_theme(theme_dir: Path) -> PdfTheme:
    try:
        theme = load_plugin(theme_dir / 'theme.py', base_class=PdfTheme)()
    except FileNotFoundError:
        theme = PdfTheme()

    with suppress(AssertionError):
        sty = theme_dir / 'theme.sty'
        assert sty.exists()
        theme.sty = sty

    with suppress(AssertionError):
        cover = theme_dir / 'cover.tex'
        assert cover.exists()
        theme.cover = cover

    return theme
