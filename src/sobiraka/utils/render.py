from functools import cache
from typing import Awaitable

import jinja2


@cache
def _jinja() -> jinja2.Environment:
    return jinja2.Environment(enable_async=True, undefined=jinja2.StrictUndefined)


def render(template: str, *args, **kwargs) -> Awaitable[str]:
    return _jinja().from_string(template).render_async(*args, **kwargs)
