from argparse import ArgumentParser
from asyncio import run
from pathlib import Path

from sobiraka.models.book import Book
from sobiraka.processors import DocxBuilder, PdfBuilder, SpellChecker
from sobiraka.runtime import RT
from sobiraka.utils import validate_dictionary


async def async_main():  # pragma: no cover
    parser = ArgumentParser()
    parser.add_argument('--tmpdir', type=Path, default=Path('build'))

    commands = parser.add_subparsers(title='commands', dest='command')

    cmd_docx = commands.add_parser('docx', help='Build DOCX file.')
    cmd_docx.add_argument('source', type=Path)
    cmd_docx.add_argument('target', type=Path)

    cmd_pdf = commands.add_parser('pdf', help='Build PDF file.')
    cmd_pdf.add_argument('source', type=Path)
    cmd_pdf.add_argument('target', type=Path)

    cmd_spellcheck = commands.add_parser('spellcheck', help='Check spelling with Hunspell.')
    cmd_spellcheck.add_argument('source', type=Path)

    cmd_validate_dictionary = commands.add_parser('validate_dictionary', help='Validate and fix Hunspell dictionary.')
    cmd_validate_dictionary.add_argument('dic', type=Path)
    cmd_validate_dictionary.add_argument('--autofix', action='store_true')

    args = parser.parse_args()
    RT.TMP = args.tmpdir

    match args.command:
        case 'pdf':
            book = Book.from_manifest(args.source)
            builder = PdfBuilder(book)
            exit_code = await builder.run(args.target)

        case 'docx':
            book = Book.from_manifest(args.source)
            builder = DocxBuilder(book)
            exit_code = await builder.run(args.target)

        case 'spellcheck':
            book = Book.from_manifest(args.source)
            checker = SpellChecker(book)
            exit_code = await checker.run()

        case 'validate_dictionary':
            exit_code = validate_dictionary(args.dic, autofix=args.autofix)

        case _:
            raise NotImplementedError(args.command)
    exit(exit_code or 0)


def main():
    run(async_main())


if __name__ == '__main__':
    main()
