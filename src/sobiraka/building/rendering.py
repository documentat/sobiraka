import logging
import sys
from asyncio import create_subprocess_exec
from io import StringIO
from pathlib import Path
from shutil import copyfile
from subprocess import DEVNULL, PIPE
from typing import Awaitable

import panflute
from panflute import Doc

from sobiraka.models import Book, Page
from sobiraka.runtime import RT


def print_errors(book: Book) -> bool:
    errors_found: bool = False
    for page in book.pages:
        if page.errors:
            message = f'Errors in {page.relative_path}:'
            errors = sorted(page.errors, key=lambda e: (e.__class__.__name__, e))
            for error in errors:
                message += f'\n    {error}'
            message += '\n'
            print(message, file=sys.stderr)
            errors_found = True
    return errors_found


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


async def generate_latex(page: Page):
    await page.processed2.wait()

    if len(page.doc.content) == 0:
        page.latex = b''

    else:
        with StringIO() as stringio:
            panflute.dump(page.doc, stringio)
            json_bytes = stringio.getvalue().encode('utf-8')

        pandoc = await create_subprocess_exec(
            'pandoc',
            '--from', 'json',
            '--to', 'latex-smart',
            '--resource-path', page.book.root / '_images',
            '--wrap', 'none',
            stdin=PIPE,
            stdout=PIPE)
        pandoc.stdin.write(json_bytes)
        pandoc.stdin.close()
        await pandoc.wait()
        assert pandoc.returncode == 0
        page.latex = await pandoc.stdout.read()

    if RT.TMP:
        (RT.TMP / 'content' / page.relative_path.with_suffix('.tex')).write_bytes(page.latex)


async def render_pdf(book: Awaitable[Book], output: Path):
    book = await book
    output.parent.mkdir(parents=True, exist_ok=True)

    for page in book.pages:
        page.latex_generated.start()

    big_doc = Doc()
    for page in book.pages:
        await page.latex_generated.wait()
        big_doc.content.extend(page.doc.content)

    if print_errors(book):
        raise Exception

    xelatex_workdir = RT.TMP / f'tex-{book.id}'
    xelatex_workdir.mkdir(parents=True, exist_ok=True)
    for item in xelatex_workdir.iterdir():
        if item.is_dir():
            item.rmdir()
        else:
            item.unlink()
    with open(xelatex_workdir / 'build.tex', 'wb') as latex_output:
        header_path = RT.FILES / 'header.sty'
        latex_output.write(header_path.read_bytes())
        latex_output.write(b'\n\n\\begin{document}\n\\begin{sloppypar}')

        for page in book.pages:
            await page.latex_generated.wait()
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% ' + bytes(page.relative_path) + b'\n')
            latex_output.write(page.latex)

        latex_output.write(b'\n\n' + (80 * b'%'))
        latex_output.write(b'\n\n\\end{sloppypar}\n\\end{document}')

    xelatex = await create_subprocess_exec(
        'xelatex',
        'build.tex',
        '-halt-on-error',
        cwd=xelatex_workdir,
        stdin=DEVNULL,
        stdout=DEVNULL)
    await xelatex.wait()
    assert xelatex.returncode == 0
    copyfile(xelatex_workdir / 'build.pdf', output)
