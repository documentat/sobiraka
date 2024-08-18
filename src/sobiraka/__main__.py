import sys
from argparse import ArgumentParser
from asyncio import run

from sobiraka.cache import init_cache
from sobiraka.linter import Linter
from sobiraka.models.load import load_project
from sobiraka.processing import HtmlBuilder, PdfBuilder, run_with_progressbar
from sobiraka.runtime import RT
from sobiraka.translating import changelog, check_translations
from sobiraka.utils import AbsolutePath, absolute_or_relative, validate_dictionary


async def async_main():
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    parser = ArgumentParser()
    parser.add_argument('--tmpdir', type=AbsolutePath, default=AbsolutePath('build'))

    cache_or_no_cache = parser.add_mutually_exclusive_group()
    cache_or_no_cache.add_argument('--no-cache', action='store_true')
    cache_or_no_cache.add_argument('--cache', type=AbsolutePath, default=AbsolutePath('.cache'))

    commands = parser.add_subparsers(title='commands', dest='command')

    cmd_html = commands.add_parser('html', help='Build HTML site.')
    cmd_html.add_argument('config', metavar='CONFIG', type=AbsolutePath)
    cmd_html.add_argument('--output', type=AbsolutePath, default=AbsolutePath('build/html'))
    cmd_html.add_argument('--hide-index-html', action='store_true', help='Remove the "index.html" part from links.')

    cmd_pdf = commands.add_parser('pdf', help='Build PDF file.')
    cmd_pdf.add_argument('config', metavar='CONFIG', type=AbsolutePath)
    cmd_pdf.add_argument('volume', nargs='?')
    cmd_pdf.add_argument('--output', type=AbsolutePath, default=AbsolutePath('build/pdf'))

    cmd_lint = commands.add_parser('lint', help='Check a volume for various issues.')
    cmd_lint.add_argument('config', metavar='CONFIG', type=AbsolutePath)
    cmd_lint.add_argument('volume', nargs='?')

    cmd_validate_dictionary = commands.add_parser('validate_dictionary',
                                                  help='Validate and fix Hunspell dictionary.')
    cmd_validate_dictionary.add_argument('dic', type=AbsolutePath)
    cmd_validate_dictionary.add_argument('--autofix', action='store_true')

    cmd_check_translations = commands.add_parser('check_translations',
                                                 help='Display translation status of the project.')
    cmd_check_translations.add_argument('config', metavar='CONFIG', type=AbsolutePath)
    cmd_check_translations.add_argument('--strict', action='store_true')

    cmd_changelog = commands.add_parser('changelog',
                                        help='Display changes in translation versions between two git commits.')
    cmd_changelog.add_argument('config', metavar='CONFIG', type=AbsolutePath)
    cmd_changelog.add_argument('commit1')
    cmd_changelog.add_argument('commit2', default='HEAD')

    args = parser.parse_args()
    RT.TMP = args.tmpdir

    if not args.no_cache:
        init_cache(args.cache)  # TODO uses $SRC/.cache

    if args.command is None:
        parser.print_help()
        exit_code = 1

    else:
        cmd = commands.choices.get(args.command)

        if cmd is cmd_html:
            project = load_project(args.config)
            builder = HtmlBuilder(project, args.output, hide_index_html=args.hide_index_html)
            exit_code = await RT.run_isolated(run_with_progressbar(builder))

        elif cmd is cmd_pdf:
            project = load_project(args.config)
            output = absolute_or_relative(args.output)

            if args.volume is not None or len(project.volumes) == 1:
                volume = project.get_volume(args.volume)
                if output.suffix.lower() != '.pdf':
                    output /= f'{volume.config.title}.pdf'
                print(f'Building {output.name!r}...', file=sys.stderr)
                builder = PdfBuilder(volume, output)
                exit_code = await RT.run_isolated(run_with_progressbar(builder))

            else:
                assert output.suffix.lower() != '.pdf'
                exit_code = 0
                for volume in project.volumes:
                    output_file = output / f'{volume.config.title}.pdf'
                    print(f'Building {output_file.name!r}...', file=sys.stderr)
                    builder = PdfBuilder(volume, output_file)
                    exit_code = await RT.run_isolated(run_with_progressbar(builder))
                    if exit_code != 0:
                        break

        elif cmd is cmd_lint:
            project = load_project(args.config)
            volume = project.get_volume(args.volume)
            linter = Linter(volume)
            exit_code = await RT.run_isolated(run_with_progressbar(linter))

        elif cmd is cmd_validate_dictionary:
            exit_code = validate_dictionary(args.dic, autofix=args.autofix)

        elif cmd is cmd_check_translations:
            project = load_project(args.config)
            exit_code = check_translations(project, strict=args.strict)

        elif cmd is cmd_changelog:
            exit_code = changelog(args.config, args.commit1, args.commit2)

        else:
            raise NotImplementedError(args.command)

    sys.exit(exit_code or 0)


def main():
    run(async_main())


if __name__ == '__main__':
    main()
