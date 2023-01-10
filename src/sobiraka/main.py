from argparse import ArgumentParser
from asyncio import run, TaskGroup
from pathlib import Path

from sobiraka.building.rendering import render_docx, render_pdf
from sobiraka.models.book import Book
from sobiraka.runtime import RT


async def main():  # pragma: no cover
    parser = ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--docx', type=Path)
    parser.add_argument('--pdf', type=Path)
    parser.add_argument('--tmpdir', type=Path, default=Path('build'))
    args = parser.parse_args()

    source: Path = args.source
    RT.TMP = args.tmpdir

    async with TaskGroup() as tasks:
        if args.docx:
            book = Book.from_manifest(source)
            tasks.create_task(render_docx(book, args.docx))
        if args.pdf:
            book = Book.from_manifest(source)
            tasks.create_task(render_pdf(book, args.pdf))


if __name__ == '__main__':
    run(main())