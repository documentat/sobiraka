import sys
from argparse import ArgumentParser, Namespace
from asyncio import run
from typing import Iterable

from sobiraka.models import Document
from sobiraka.models.load import load_project
from sobiraka.processing.latex import LatexBuilder
from sobiraka.processing.markdown import MarkdownBuilder
from sobiraka.processing.weasyprint import WeasyPrintBuilder
from sobiraka.processing.web import WebBuilder
from sobiraka.prover import Prover
from sobiraka.report import run_beautifully
from sobiraka.runtime import RT
from sobiraka.translating import check_translations
from sobiraka.utils import AbsolutePath, DictionaryValidator, parse_vars

SOBIRAKA_YAML = AbsolutePath('sobiraka.yaml')


async def async_main():
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    parser = ArgumentParser()
    parser.add_argument('--version', action='store_true')
    parser.add_argument('--tmpdir', type=AbsolutePath, default=AbsolutePath('build'))

    commands = parser.add_subparsers(title='commands', dest='command')

    cmd_web = commands.add_parser('web', help='Build web documentation.')
    cmd_web.add_argument('--config', metavar='CONFIG', type=AbsolutePath, default=SOBIRAKA_YAML)
    cmd_web.add_argument('--output', type=AbsolutePath, default=AbsolutePath('build/web'))
    cmd_web.add_argument('--hide-index-html', action='store_true', help='Remove the "index.html" part from links.')

    cmd_pdf = commands.add_parser('pdf', help='Build PDF file via WeasyPrint.')
    cmd_pdf.add_argument('document', nargs='?')
    cmd_pdf.add_argument('--config', metavar='CONFIG', type=AbsolutePath, default=SOBIRAKA_YAML)
    cmd_pdf.add_argument('--output', type=AbsolutePath, default=AbsolutePath('build/pdf'))

    cmd_latex = commands.add_parser('latex', help='Build PDF file fia LaTeX.')
    cmd_latex.add_argument('document', nargs='?')
    cmd_latex.add_argument('--config', metavar='CONFIG', type=AbsolutePath, default=SOBIRAKA_YAML)
    cmd_latex.add_argument('--output', type=AbsolutePath, default=AbsolutePath('build/pdf'))

    cmd_markdown = commands.add_parser('markdown', help='Build Markdown file.')
    cmd_markdown.add_argument('document', nargs='?')
    cmd_markdown.add_argument('--config', metavar='CONFIG', type=AbsolutePath, default=SOBIRAKA_YAML)
    cmd_markdown.add_argument('--output', type=AbsolutePath, default=AbsolutePath('build/markdown'))

    cmd_prover = commands.add_parser('prover', help='Check a document for various issues.')
    cmd_prover.add_argument('document', nargs='?')
    cmd_prover.add_argument('--config', metavar='CONFIG', type=AbsolutePath, default=SOBIRAKA_YAML)
    cmd_prover.add_argument('--var', metavar='KEY[=VALUE]', action='append')

    cmd_validate_dictionary = commands.add_parser('validate_dictionary',
                                                  help='Validate and fix Hunspell dictionary.')
    cmd_validate_dictionary.add_argument('dic', type=AbsolutePath)
    cmd_validate_dictionary.add_argument('--autofix', action='store_true')

    cmd_check_translations = commands.add_parser('check_translations',
                                                 help='Display translation status of the project.')
    cmd_check_translations.add_argument('--config', metavar='CONFIG', type=AbsolutePath, default=SOBIRAKA_YAML)
    cmd_check_translations.add_argument('--strict', action='store_true')

    args = parser.parse_args()
    RT.TMP = args.tmpdir

    if args.version:
        print((AbsolutePath(__file__).parent / 'VERSION').read_text().strip())
        exit_code = 0

    elif args.command is None:
        parser.print_help()
        exit_code = 1

    else:
        cmd = commands.choices.get(args.command)

        if cmd is cmd_web:
            project = load_project(args.config)
            builder = WebBuilder(project, args.output, hide_index_html=args.hide_index_html)
            with run_beautifully():
                exit_code = await RT.run_isolated(builder.run())

        elif cmd is cmd_latex:
            for document, output in selected_documents(args, autosuffix='.pdf'):
                builder = LatexBuilder(document, output)
                with run_beautifully():
                    exit_code = await RT.run_isolated(builder.run())
                    if exit_code != 0:
                        break

        elif cmd is cmd_pdf:
            for document, output in selected_documents(args, autosuffix='.pdf'):
                builder = WeasyPrintBuilder(document, output)
                with run_beautifully():
                    exit_code = await RT.run_isolated(builder.run())
                    if exit_code != 0:
                        break

        elif cmd is cmd_markdown:
            for document, output in selected_documents(args):
                builder = MarkdownBuilder(document, output)
                with run_beautifully():
                    exit_code = await RT.run_isolated(builder.run())
                    if exit_code != 0:
                        break

        elif cmd is cmd_prover:
            project = load_project(args.config)
            document = project.get_document(args.document)
            prover = Prover(document, parse_vars(args.var or ()))
            with run_beautifully():
                exit_code = await RT.run_isolated(prover.run())

        elif cmd is cmd_validate_dictionary:
            dic_path = args.dic
            aff_path = dic_path.with_suffix('.aff')
            assert args.dic.suffix == '.dic'
            exit_code = DictionaryValidator(aff_path, dic_path).run(args.autofix)

        elif cmd is cmd_check_translations:
            project = load_project(args.config)
            exit_code = check_translations(project, strict=args.strict)

        else:
            raise NotImplementedError(args.command)

    sys.exit(exit_code or 0)


def selected_documents(args: Namespace, *, autosuffix: str = '') -> Iterable[tuple[Document, AbsolutePath]]:
    project = load_project(args.config)
    output = AbsolutePath(args.output)

    if args.document is not None or len(project.documents) == 1:
        document = project.get_document(args.document)
        if autosuffix:
            if output.suffix.lower() != autosuffix:
                output /= document.config.title + autosuffix
        print(f'Building {output.name!r}...', file=sys.stderr)
        yield document, output

    else:
        if autosuffix:
            assert output.suffix.lower() != autosuffix
        for document in project.documents:
            output_file = output / document.config.title + autosuffix
            print(f'Building {output_file.name!r}...', file=sys.stderr)
            yield document, output_file


def main():
    run(async_main())


if __name__ == '__main__':
    main()
