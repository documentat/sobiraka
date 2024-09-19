from abc import ABCMeta
from contextlib import suppress
from dataclasses import dataclass

import jinja2

from sobiraka.utils import AbsolutePath
from .plugin import Plugin, load_plugin


@dataclass
class WeasyPrintTheme(Plugin, metaclass=ABCMeta):
    theme_dir: AbsolutePath
    static_dir: AbsolutePath
    page_template: jinja2.Template


def load_weasyprint_theme(theme_dir: AbsolutePath) -> WeasyPrintTheme:
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(theme_dir),
        enable_async=True,
        undefined=jinja2.StrictUndefined,
        comment_start_string='{{#',
        comment_end_string='#}}')
    page_template = jinja_env.get_template('page.html')

    static_dir = theme_dir / '_static'

    theme_class = WeasyPrintTheme
    with suppress(FileNotFoundError, AssertionError):
        theme_class = load_plugin(theme_dir / 'theme.py', base_class=WeasyPrintTheme)

    return theme_class(theme_dir, static_dir, page_template)
