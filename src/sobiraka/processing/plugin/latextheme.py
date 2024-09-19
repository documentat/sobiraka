from abc import ABCMeta
from contextlib import suppress
from dataclasses import dataclass

from sobiraka.utils import AbsolutePath
from .plugin import Plugin, load_plugin


@dataclass
class LatexTheme(Plugin, metaclass=ABCMeta):
    """
    A theme for LatexBuilder.

    It may or may not provide multiple files that will be included at the beginning of the resulting LaTeX document.

    Additionally, the theme may contain its own implementation of functions for additional AST processing.
    The implementation will be called via Dispatcher.process_container().
    """

    style: AbsolutePath = None
    """LaTeX code to be included at the very beginning, even before ``\\begin{document}``."""

    cover: AbsolutePath = None
    """LaTeX code to be included immediately after the document environment began."""

    toc: AbsolutePath = None
    """LaTeX code to be included after the cover."""


def load_latex_theme(theme_dir: AbsolutePath) -> LatexTheme:
    theme = LatexTheme()
    with suppress(FileNotFoundError):
        theme = load_plugin(theme_dir / 'theme.py', base_class=LatexTheme)()
    theme.style = _try_find_file(theme_dir, 'style.sty')
    theme.cover = _try_find_file(theme_dir, 'cover.tex')
    theme.toc = _try_find_file(theme_dir, 'toc.tex')
    return theme


def _try_find_file(base: AbsolutePath, filename: str) -> AbsolutePath | None:
    path = base / filename
    if path.exists():
        return path
    return None
