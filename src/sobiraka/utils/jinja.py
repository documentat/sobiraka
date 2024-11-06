import jinja2

from sobiraka.utils import AbsolutePath


def configured_jinja(template_dir: AbsolutePath) -> jinja2.Environment:
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        enable_async=True,
        undefined=jinja2.StrictUndefined,
        comment_start_string='{{#',
        comment_end_string='#}}')
