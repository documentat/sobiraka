from asyncio import create_subprocess_exec
from io import BytesIO
from pathlib import Path
from subprocess import PIPE

import panflute
import yaml

from sobiraka.models import Book, Page
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
        page.path,
        '--from', syntax,
        '--to', 'json',
        stdout=PIPE)
    await pandoc.wait()
    assert pandoc.returncode == 0
    json_bytes = await pandoc.stdout.read()

    page.doc = panflute.load(BytesIO(json_bytes))
    save_debug_json('s0', page)
