from abc import ABCMeta
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
    theme.sty = _try_find_file(theme_dir, 'theme.sty')
    theme.cover = _try_find_file(theme_dir, 'cover.tex')
    return theme


def _try_find_file(base: Path, filename: str) -> Path | None:
    path = base / filename
    if path.exists():
        return path
    return None
