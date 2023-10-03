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
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    parser = ArgumentParser()
    parser.add_argument('--tmpdir', type=absolute_path, default=absolute_path('build'))

    commands = parser.add_subparsers(title='commands', dest='command')

    cmd_html = commands.add_parser('html', help='Build HTML site.')
    cmd_html.add_argument('project', type=absolute_path)
    cmd_html.add_argument('--output', type=absolute_path, default=absolute_path('build/html'))
    cmd_html.add_argument('--hide-index-html', action='store_true', help='Remove the "index.html" part from links.')

    cmd_pdf = commands.add_parser('pdf', help='Build PDF file.')
    cmd_pdf.add_argument('project', type=absolute_path)
    cmd_pdf.add_argument('volume', nargs='?')
    cmd_pdf.add_argument('--output', type=absolute_path, default=absolute_path('build/pdf'))

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
            exit_code = await HtmlBuilder(project, args.output, hide_index_html=args.hide_index_html).run()

        elif cmd is cmd_pdf:
            project = load_project(args.project)
            output: Path = args.output

            if args.volume is not None or len(project.volumes) == 1:
                volume = project.volumes[0]
                if output.suffix.lower() != '.pdf':
                    output /= f'{volume.config.title}.pdf'
                exit_code = await PdfBuilder(volume, output).run()

            else:
                assert output.suffix.lower() != '.pdf'
                exit_code = 0
                for volume in project.volumes:
                    output_file = output / f'{volume.config.title}.pdf'
                    print(f'Building {output_file.name!r}...', file=sys.stderr)
                    exit_code = await PdfBuilder(volume, output_file).run()
                    if exit_code != 0:
                        break

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
