from asyncio import create_subprocess_exec
from io import BytesIO
from subprocess import PIPE

import panflute

from sobiraka.models import Page
from sobiraka.utils import save_debug_json


async def load_page(page: Page):

    match page.path.suffix:
        case '.md':
            syntax = 'markdown'
        case '.rst':
            syntax = 'rst-auto_identifiers'
        case _:
            raise NotImplementedError(page.path.suffix)

    pandoc = await create_subprocess_exec(
        'pandoc',
        '--from', syntax,
        '--to', 'json',
        stdin=PIPE,
        stdout=PIPE)
    json_bytes, _ = await pandoc.communicate(page.path.read_bytes())
    assert pandoc.returncode == 0

    page.doc = panflute.load(BytesIO(json_bytes))
    save_debug_json('s0', page)