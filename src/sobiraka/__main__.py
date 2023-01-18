from argparse import ArgumentParser
from asyncio import run
from pathlib import Path

from sobiraka.models.book import Book
from sobiraka.processors import DocxBuilder, PdfBuilder, SpellChecker
from sobiraka.runtime import RT


async def async_main():  # pragma: no cover
    parser = ArgumentParser()
    parser.add_argument('--tmpdir', type=Path, default=Path('build'))

    commands = parser.add_subparsers(title='commands', dest='command')

    parser_docx = commands.add_parser('docx', help='Build DOCX file.')
    parser_docx.add_argument('source', type=Path)
    parser_docx.add_argument('PATH', type=Path)

    parser_pdf = commands.add_parser('pdf', help='Build PDF file.')
    parser_pdf.add_argument('source', type=Path)
    parser_pdf.add_argument('PATH', type=Path)

    parser_spellcheck = commands.add_parser('spellcheck', help='Check spelling with Hunspell.')
    parser_spellcheck.add_argument('source', type=Path)

    args = parser.parse_args()
    RT.TMP = args.tmpdir

    source: Path = args.source
    book = Book(source)

    match args.command:
        case 'pdf':
            exit_code = await PdfBuilder(book).run(args.pdf)
        case 'docx':
            exit_code = await DocxBuilder(book).run(args.docx)
        case 'spellcheck':
            exit_code = await SpellChecker(book).run()
        case _:
            raise NotImplementedError(args.command)
    exit(exit_code or 0)


def main():
    run(async_main())


if __name__ == '__main__':
    main()
