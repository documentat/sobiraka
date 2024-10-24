from abc import ABCMeta
from contextlib import suppress
from functools import cached_property
from mimetypes import guess_type
from typing import TextIO

import jinja2
from six import StringIO

from sobiraka.utils import AbsolutePath
from .plugin import Plugin, load_plugin


class WeasyPrintTheme(Plugin, metaclass=ABCMeta):
    def __init__(self, theme_dir: AbsolutePath):
        super().__init__()
        self.theme_dir: AbsolutePath = theme_dir
        self.static_pseudofiles: dict[str, tuple[str, str]] = {}

    @cached_property
    def page_template(self) -> jinja2.Template:
        jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.theme_dir),
            enable_async=True,
            undefined=jinja2.StrictUndefined,
            comment_start_string='{{#',
            comment_end_string='#}}')
        return jinja_env.get_template('print.html')

    def open_static_file(self, path: str) -> tuple[str, TextIO]:
        try:
            mime_type, content = self.static_pseudofiles[path]
            return mime_type, StringIO(content)
        except KeyError:
            path = self.theme_dir / '_static' / path
            mime_type, _ = guess_type(path, strict=False)
            return mime_type, path.open()


def load_weasyprint_theme(theme_dir: AbsolutePath) -> WeasyPrintTheme:
    theme_class = WeasyPrintTheme
    with suppress(FileNotFoundError, AssertionError):
        theme_class = load_plugin(theme_dir / 'theme.py', base_class=WeasyPrintTheme)
    return theme_class(theme_dir)
