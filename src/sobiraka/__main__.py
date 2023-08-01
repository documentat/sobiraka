import sys
from argparse import ArgumentParser
from asyncio import run
from pathlib import Path

from sobiraka.linter import Linter
from sobiraka.models.load import load_project
from sobiraka.processing import HtmlBuilder, PdfBuilder
from sobiraka.runtime import RT
from sobiraka.translating import check_translations, changelog
from sobiraka.utils import validate_dictionary


async def async_main():
    # pylint: disable=too-many-statements

    parser = ArgumentParser()
    parser.add_argument('--tmpdir', type=absolute_path, default=absolute_path('build'))

    commands = parser.add_subparsers(title='commands', dest='command')

    cmd_html = commands.add_parser('html', help='Build HTML site.')
    cmd_html.add_argument('project', type=absolute_path)
    cmd_html.add_argument('target', type=absolute_path)

    cmd_pdf = commands.add_parser('pdf', help='Build PDF file.')
    cmd_pdf.add_argument('project', type=absolute_path)
    cmd_pdf.add_argument('volume', nargs='?')
    cmd_pdf.add_argument('target', type=absolute_path)

    cmd_lint = commands.add_parser('lint', help='Check a volume for various issues.')
    cmd_lint.add_argument('project', type=absolute_path)
    cmd_lint.add_argument('volume', nargs='?')

    cmd_validate_dictionary = commands.add_parser('validate_dictionary',
                                                  help='Validate and fix Hunspell dictionary.')
    cmd_validate_dictionary.add_argument('dic', type=absolute_path)
    cmd_validate_dictionary.add_argument('--autofix', action='store_true')

    cmd_check_translations = commands.add_parser('check_translations',
                                                 help='Display translation status of the project.')
    cmd_check_translations.add_argument('project', type=absolute_path)
    cmd_check_translations.add_argument('--strict', action='store_true')

    cmd_changelog = commands.add_parser('changelog',
                                   help='Display changes in translation versions between two git commits.')
    cmd_changelog.add_argument('project', type=absolute_path)
    cmd_changelog.add_argument('commit1')
    cmd_changelog.add_argument('commit2', default='HEAD')

    args = parser.parse_args()
    RT.TMP = args.tmpdir

    if args.command is None:
        parser.print_help()
        exit_code = 1

    else:
        cmd = commands.choices.get(args.command)

        if cmd is cmd_html:
            project = load_project(args.project)
            exit_code = await HtmlBuilder(project, args.target).run()

        elif cmd is cmd_pdf:
            project = load_project(args.project)
            volume = project.get_volume(args.volume)
            exit_code = await PdfBuilder(volume, args.target).run()

        elif cmd is cmd_lint:
            project = load_project(args.project)
            volume = project.get_volume(args.volume)
            linter = Linter(volume)
            exit_code = await linter.check()
            if exit_code != 0:
                linter.print_issues()

        elif cmd is cmd_validate_dictionary:
            exit_code = validate_dictionary(args.dic, autofix=args.autofix)

        elif cmd is cmd_check_translations:
            project = load_project(args.project)
            exit_code = check_translations(project, strict=args.strict)

        elif cmd is cmd_changelog:
            exit_code = changelog(args.project, args.commit1, args.commit2)

        else:
            raise NotImplementedError(args.command)

    sys.exit(exit_code or 0)


def absolute_path(path: str) -> Path:
    return (Path() / path).resolve().absolute()


def main():
    run(async_main())


if __name__ == '__main__':
    main()
