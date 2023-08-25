from abc import ABCMeta
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

import jinja2

from .plugin import Plugin, load_plugin


@dataclass
class HtmlTheme(Plugin, metaclass=ABCMeta):
    page_template: jinja2.Template
    static_dir: Path


def load_html_theme(theme_dir: Path) -> HtmlTheme:
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(theme_dir),
        enable_async=True,
        undefined=jinja2.StrictUndefined,
        comment_start_string='{{#',
        comment_end_string='#}}')
    page_template = jinja_env.get_template('page.html')

    static_dir = theme_dir / '_static'

    theme_class = HtmlTheme
    with suppress(FileNotFoundError):
        theme_class = load_plugin(theme_dir / 'theme.py', base_class=HtmlTheme)

    return theme_class(page_template, static_dir)
