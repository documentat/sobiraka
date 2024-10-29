from abc import ABCMeta

from sobiraka.utils import AbsolutePath
from .plugin import Theme


class LatexTheme(Theme, metaclass=ABCMeta):
    """
    A theme for LatexBuilder.

    It may or may not provide multiple files that will be included at the beginning of the resulting LaTeX document.

    Additionally, the theme may contain its own implementation of functions for additional AST processing.
    The implementation will be called via Dispatcher.process_container().
    """

    def __init__(self, theme_dir: AbsolutePath):
        super().__init__(theme_dir)

        self.style = _try_find_file(theme_dir, 'style.sty')
        """LaTeX code to be included at the very beginning, even before ``\\begin{document}``."""

        self.cover = _try_find_file(theme_dir, 'cover.tex')
        """LaTeX code to be included immediately after the document environment began."""

        self.toc = _try_find_file(theme_dir, 'toc.tex')
        """LaTeX code to be included after the cover."""


def _try_find_file(base: AbsolutePath, filename: str) -> AbsolutePath | None:
    path = base / filename
    if path.exists():
        return path
    return None
