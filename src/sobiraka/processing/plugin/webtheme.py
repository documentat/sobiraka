from abc import ABCMeta
from contextlib import suppress
from dataclasses import dataclass, field

import jinja2

from sobiraka.utils import AbsolutePath
from .plugin import Plugin, load_plugin


@dataclass
class WebTheme(Plugin, metaclass=ABCMeta):
    """
    A theme for generating HTML.

    It provides a Jinja template that will be used for rendering each HTML page
    and, optionally, a directory with static files required for the template.

    Additionally, the theme may contain its own implementation of functions for additional AST processing.
    The implementation will be called via Dispatcher.process_container().
    """
    theme_dir: AbsolutePath
    static_dir: AbsolutePath
    page_template: jinja2.Template
    sass_files: dict[str, str] = field(default_factory=dict)


def load_web_theme(theme_dir: AbsolutePath) -> WebTheme:
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(theme_dir),
        enable_async=True,
        undefined=jinja2.StrictUndefined,
        comment_start_string='{{#',
        comment_end_string='#}}')
    page_template = jinja_env.get_template('web.html')

    static_dir = theme_dir / '_static'

    theme_class = WebTheme
    with suppress(FileNotFoundError):
        theme_class = load_plugin(theme_dir / 'theme.py', base_class=WebTheme)

    return theme_class(theme_dir, static_dir, page_template)
