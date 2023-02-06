from argparse import ArgumentParser
from asyncio import run
from pathlib import Path

from sobiraka.linter import Linter
from sobiraka.models import Book
from sobiraka.processing import DocxBuilder, PdfBuilder, TxtBuilder
from sobiraka.runtime import RT
from sobiraka.utils import validate_dictionary


async def async_main():  # pragma: no cover
    parser = ArgumentParser()
    parser.add_argument('--tmpdir', type=absolute_path, default=absolute_path('build'))

    commands = parser.add_subparsers(title='commands', dest='command')

    cmd_docx = commands.add_parser('docx', help='Build DOCX file.')
    cmd_docx.add_argument('source', type=absolute_path)
    cmd_docx.add_argument('target', type=absolute_path)

    cmd_pdf = commands.add_parser('pdf', help='Build PDF file.')
    cmd_pdf.add_argument('source', type=absolute_path)
    cmd_pdf.add_argument('target', type=absolute_path)

    cmd_txt = commands.add_parser('txt', help='Build TXT files.')
    cmd_txt.add_argument('source', type=absolute_path)
    cmd_txt.add_argument('target', type=absolute_path)

    cmd_lint = commands.add_parser('lint', help='Check book for various issues.')
    cmd_lint.add_argument('source', type=absolute_path)

    cmd_validate_dictionary = commands.add_parser('validate_dictionary', help='Validate and fix Hunspell dictionary.')
    cmd_validate_dictionary.add_argument('dic', type=absolute_path)
    cmd_validate_dictionary.add_argument('--autofix', action='store_true')

    args = parser.parse_args()
    RT.TMP = args.tmpdir

    match args.command:
        case None:
            parser.print_help()
            exit_code = 1

        case 'docx':
            book = Book.from_manifest(args.source)
            exit_code = await DocxBuilder(book).run(args.target)

        case 'pdf':
            book = Book.from_manifest(args.source)
            exit_code = await PdfBuilder(book).run(args.target)

        case 'txt':
            book = Book.from_manifest(args.source)
            exit_code = await TxtBuilder(book).run(args.target)

        case 'lint':
            book = Book.from_manifest(args.source)
            exit_code = await Linter(book).check()

        case 'validate_dictionary':
            exit_code = validate_dictionary(args.dic, autofix=args.autofix)

        case _:
            raise NotImplementedError(args.command)
    exit(exit_code or 0)


def absolute_path(path: str) -> Path:
    return (Path() / path).resolve().absolute()


def main():
    run(async_main())


if __name__ == '__main__':
    main()