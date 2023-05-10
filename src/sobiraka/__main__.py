import sys
from argparse import ArgumentParser
from asyncio import run
from pathlib import Path

from sobiraka.linter import Linter
from sobiraka.models.load import load_project
from sobiraka.processing import HtmlBuilder, PdfBuilder
from sobiraka.runtime import RT
from sobiraka.utils import validate_dictionary


async def async_main():  # pragma: no cover
    parser = ArgumentParser()
    parser.add_argument('--tmpdir', type=absolute_path, default=absolute_path('build'))

    commands = parser.add_subparsers(title='commands', dest='command')

    cmd_html = commands.add_parser('html', help='Build HTML site.')
    cmd_html.add_argument('source', type=absolute_path)
    cmd_html.add_argument('target', type=absolute_path)

    cmd_pdf = commands.add_parser('pdf', help='Build PDF file.')
    cmd_pdf.add_argument('source', type=absolute_path)
    cmd_pdf.add_argument('volume', nargs='?')
    cmd_pdf.add_argument('target', type=absolute_path)

    cmd_lint = commands.add_parser('lint', help='Check a volume for various issues.')
    cmd_lint.add_argument('source', type=absolute_path)
    cmd_lint.add_argument('volume', nargs='?')

    cmd_validate_dictionary = commands.add_parser('validate_dictionary', help='Validate and fix Hunspell dictionary.')
    cmd_validate_dictionary.add_argument('dic', type=absolute_path)
    cmd_validate_dictionary.add_argument('--autofix', action='store_true')

    args = parser.parse_args()
    RT.TMP = args.tmpdir

    match args.command:
        case None:
            parser.print_help()
            exit_code = 1

        case 'html':
            project = load_project(args.source)
            exit_code = await HtmlBuilder(project).run(args.target)

        case 'pdf':
            project = load_project(args.source)
            volume = project.get_volume(args.volume)
            exit_code = await PdfBuilder(volume).run(args.target)

        case 'lint':
            project = load_project(args.source)
            volume = project.get_volume(args.volume)
            linter = Linter(volume)
            exit_code = await linter.check()
            if exit_code != 0:
                linter.print_issues()

        case 'validate_dictionary':
            exit_code = validate_dictionary(args.dic, autofix=args.autofix)

        case _:
            raise NotImplementedError(args.command)
    sys.exit(exit_code or 0)


def absolute_path(path: str) -> Path:
    return (Path() / path).resolve().absolute()


def main():
    run(async_main())


if __name__ == '__main__':
    main()
