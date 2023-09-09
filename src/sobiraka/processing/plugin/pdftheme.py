from abc import ABCMeta
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from .plugin import Plugin, load_plugin


@dataclass
class PdfTheme(Plugin, metaclass=ABCMeta):
    """
    A theme for generating PDF.

    It may or may not provide multiple files that will be included at the beginning of the resulting LaTeX document.

    Additionally, the theme may contain its own implementation of functions for additional AST processing.
    The implementation will be called via Dispatcher.process_container().
    """

    style: Path = None
    """LaTeX code to be included at the very beginning, even before ``\\begin{document}``."""

    cover: Path = None
    """LaTeX code to be included immediately after the document environment began."""

    toc: Path = None
    """LaTeX code to be included after the cover."""


def load_pdf_theme(theme_dir: Path) -> PdfTheme:
    theme = PdfTheme()
    with suppress(FileNotFoundError):
        theme = load_plugin(theme_dir / 'theme.py', base_class=PdfTheme)()
    theme.style = _try_find_file(theme_dir, 'style.sty')
    theme.cover = _try_find_file(theme_dir, 'cover.tex')
    theme.toc = _try_find_file(theme_dir, 'toc.tex')
    return theme


def _try_find_file(base: Path, filename: str) -> Path | None:
    path = base / filename
    if path.exists():
        return path
    return None
