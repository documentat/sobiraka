from abc import ABCMeta
from functools import cached_property
from io import StringIO
from mimetypes import guess_type
from typing import TextIO

import jinja2

from sobiraka.utils import AbsolutePath
from .plugin import Theme


class AbstractHtmlTheme(Theme, metaclass=ABCMeta):
    """
    A theme for generating HTML.

    It provides a Jinja template that will be used for rendering each HTML page
    and, optionally, a directory with static files required for the template.

    Additionally, the theme may contain its own implementation of functions for additional AST processing.
    The implementation will be called via Dispatcher.process_container().
    """
    TEMPLATE_NAME: str

    @cached_property
    def page_template(self) -> jinja2.Template:
        jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.theme_dir),
            enable_async=True,
            undefined=jinja2.StrictUndefined,
            comment_start_string='{{#',
            comment_end_string='#}}')
        return jinja_env.get_template(self.TEMPLATE_NAME)


class WebTheme(AbstractHtmlTheme, metaclass=ABCMeta):
    TEMPLATE_NAME = 'web.html'

    def __init__(self, theme_dir: AbsolutePath):
        super().__init__(theme_dir)
        self.static_dir: AbsolutePath = theme_dir / '_static'


class WeasyPrintTheme(AbstractHtmlTheme, metaclass=ABCMeta):
    TEMPLATE_NAME = 'print.html'

    def __init__(self, theme_dir: AbsolutePath):
        super().__init__(theme_dir)
        self.static_pseudofiles: dict[str, tuple[str, str]] = {}

    def open_static_file(self, path: str) -> tuple[str, TextIO]:
        try:
            mime_type, content = self.static_pseudofiles[path]
            return mime_type, StringIO(content)
        except KeyError:
            path = self.theme_dir / '_static' / path
            mime_type, _ = guess_type(path, strict=False)
            return mime_type, path.open()
