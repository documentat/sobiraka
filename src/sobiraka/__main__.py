from argparse import ArgumentParser
from asyncio import gather, run
from pathlib import Path
from typing import Awaitable

from sobiraka.builders import DocxBuilder, PdfBuilder
from sobiraka.models.book import Book
from sobiraka.runtime import RT


async def async_main():  # pragma: no cover
    parser = ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--docx', type=Path)
    parser.add_argument('--pdf', type=Path)
    parser.add_argument('--tmpdir', type=Path, default=Path('build'))
    args = parser.parse_args()

    source: Path = args.source
    RT.TMP = args.tmpdir

    book = await Book.from_manifest(source)

    tasks: list[Awaitable] = []
    if args.docx:
        tasks.append(DocxBuilder(book).build(args.docx))
    if args.pdf:
        tasks.append(PdfBuilder(book).build(args.pdf))

    await gather(*tasks)


def main():
    run(async_main())


if __name__ == '__main__':
    main()
