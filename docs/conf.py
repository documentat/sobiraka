import sys
from pathlib import Path
from typing import Any, Literal

from sphinx.application import Sphinx

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

project = 'Sobiraka'
copyright = '2023, Max Alibaev'
author = 'Max Alibaev'
release = '1.0.0'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx']

intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

templates_path = ['_templates']
exclude_patterns = []

language = 'en'

html_theme = 'furo'
html_theme_options = dict(

)
html_css_files = [
    'custom.css',
]

python_use_unqualified_type_names = True
add_module_names = False

html_static_path = ['_static']

autodoc_default_options = {
    'members': True,
    'member-order': 'alphabetical',
    'special-members': '__init__',
    'undoc-members': True,
}


def maybe_skip_member(
        app: Sphinx,
        what: Literal['module', 'class', 'exception', 'function', 'method', 'attribute'],
        name: str,
        obj: object,
        skip: bool,
        options: dict[str, Any],
) -> bool:
    return skip


def setup(app):
    app.connect('autodoc-skip-member', maybe_skip_member)
