from asyncio import create_subprocess_exec
from io import StringIO
from pathlib import Path
from subprocess import PIPE
from typing import Awaitable

import panflute
from panflute import Doc

from sobiraka.models import Book
from sobiraka.utils import print_errors


async def render_docx(book: Awaitable[Book], output: Path):
    book = await book
    output.parent.mkdir(parents=True, exist_ok=True)

    for page in book.pages:
        page.processed2.start()

    big_doc = Doc()
    for page in book.pages:
        await page.processed2.wait()
        big_doc.content.extend(page.doc.content)

    if print_errors(book):
        raise Exception

    with StringIO() as stringio:
        panflute.dump(big_doc, stringio)
        json_bytes = stringio.getvalue().encode('utf-8')

    pandoc = await create_subprocess_exec(
        'pandoc',
        '--from', 'json',
        '--to', 'docx',
        '--resource-path', book.root / '_images',
        '--output', output,
        stdin=PIPE)
    pandoc.stdin.write(json_bytes)
    pandoc.stdin.close()
    await pandoc.wait()
    assert pandoc.returncode == 0
