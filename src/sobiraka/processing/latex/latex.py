from __future__ import annotations

import os
import re
import sys
import urllib.parse
from abc import ABCMeta
from asyncio import create_subprocess_exec
from contextlib import suppress
from shutil import copyfile
from subprocess import DEVNULL, PIPE
from typing import BinaryIO, final

from panflute import Element, Header, Str, stringify
from typing_extensions import override

from sobiraka.models import DirPage, FileSystem, Page, PageHref, Status, Volume
from sobiraka.models.config import Config, Config_Latex_Headers
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, LatexInline, convert_or_none, panflute_to_bytes
from ..abstract import Processor, Theme, ThemeableVolumeBuilder
from ..abstract.processor import DisableLink
from ..load_processor import load_processor
from ..replacement import HeaderReplPara


@final
class LatexBuilder(ThemeableVolumeBuilder['LatexProcessor', 'LatexTheme']):
    def __init__(self, volume: Volume, output: AbsolutePath, **kwargs):
        super().__init__(volume, **kwargs)

        self.output: AbsolutePath = output

    def init_processor(self) -> LatexProcessor:
        fs: FileSystem = self.get_project().fs
        config: Config = self.volume.config
        processor_class = load_processor(
            convert_or_none(fs.resolve, config.web.processor),
            config.web.theme,
            LatexProcessor)
        return processor_class(self)

    def init_theme(self) -> LatexTheme:
        return LatexTheme(self.volume.config.latex.theme)

    @override
    def additional_variables(self) -> dict:
        return dict(PDF=True, LATEX=True)

    async def run(self):
        self.waiter.start()

        xelatex_workdir = RT.TMP / 'tex'
        xelatex_workdir.mkdir(parents=True, exist_ok=True)
        with open(xelatex_workdir / 'build.tex', 'wb') as latex_output:
            await self.generate_latex(latex_output)

        resources_dir = self.volume.project.fs.resolve(self.volume.config.paths.resources)
        total_runs = 3
        for _ in range(1, total_runs + 1):
            xelatex = await create_subprocess_exec(
                'xelatex',
                '-shell-escape',
                '-halt-on-error',
                'build.tex',
                cwd=xelatex_workdir,
                env=os.environ | {'TEXINPUTS': f'{resources_dir}:'},
                stdin=DEVNULL,
                stdout=DEVNULL)
            await xelatex.wait()
            if xelatex.returncode != 0:
                self.print_xelatex_error(xelatex_workdir / 'build.log')
                return 1

        self.output.parent.mkdir(parents=True, exist_ok=True)
        copyfile(xelatex_workdir / 'build.pdf', self.output)

        await self.waiter.wait_all()

        return 0

    async def generate_latex(self, latex_output: BinaryIO):
        # pylint: disable=too-many-branches

        volume = self.volume
        project = self.volume.project
        config = self.volume.config

        if config.latex.paths:
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% Paths\n\n')
            for key, value in config.latex.paths.items():
                value = self.volume.project.fs.resolve(value)
                latex_output.write(fr'\newcommand{{\{key}}}{{{value}/}}'.encode('utf-8') + b'\n')

        variables = {
            'TITLE': config.title,
            'LANG': volume.lang,
        }
        for key, value in config.variables.items():
            if re.fullmatch(r'[A-Za-z_]+', key):
                variables[key] = value
        latex_output.write(b'\n\n' + (80 * b'%'))
        latex_output.write(b'\n\n%%% Variables\n\n')
        for key, value in variables.items():
            key = key.replace('_', '')
            latex_output.write(fr'\newcommand{{\{key}}}{{{value}}}'.encode('utf-8') + b'\n')

        if self.theme.style is not None:
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% ' + self.theme.__class__.__name__.encode('utf-8') + b'\n\n')
            latex_output.write(self.theme.style.read_bytes())

        if config.latex.header:
            latex_output.write(b'\n\n')
            latex_output.write(b'\n\n%%% Project\'s custom header \n\n')
            latex_output.write(project.fs.read_bytes(config.latex.header))

        latex_output.write(b'\n\n' + (80 * b'%'))
        latex_output.write(b'\n\n\\begin{document}\n\\begin{sloppypar}')

        if self.theme.cover is not None:
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% Cover\n\n')
            latex_output.write(self.theme.cover.read_bytes())

        if config.latex.toc and self.theme.toc is not None:
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% Table of contents\n\n')
            latex_output.write(self.theme.toc.read_bytes())

        await self.waiter.wait_all()
        for page in volume.root.all_pages():
            if page.location.is_root and isinstance(page, DirPage):
                continue
            await self.waiter.wait(page, Status.FINALIZE)
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% ' + bytes(page.source.path_in_project) + b'\n\n')
            latex_output.write(RT[page].bytes)

        latex_output.write(b'\n\n' + (80 * b'%'))
        latex_output.write(b'\n\n\\end{sloppypar}\n\\end{document}')

    @override
    async def do_finalize(self, page: Page):
        if len(RT[page].doc.content) == 0:
            RT[page].bytes = b''

        else:
            pandoc = await create_subprocess_exec(
                'pandoc',
                '--from', 'json',
                '--to', 'latex-smart',
                '--wrap', 'none',
                stdin=PIPE,
                stdout=PIPE)
            pandoc.stdin.write(panflute_to_bytes(RT[page].doc))
            pandoc.stdin.close()
            await pandoc.wait()
            assert pandoc.returncode == 0
            RT[page].bytes = await pandoc.stdout.read()

            # When a LatexTheme prepends or appends some code to a Para,
            # it may leave the 'BEGIN STRIP'/'END STRIP' notes,
            # which we will now use to remove unnecessary empty lines
            RT[page].bytes = re.sub(rb'% BEGIN STRIP\n+', b'', RT[page].bytes)
            RT[page].bytes = re.sub(rb'\n+% END STRIP', b'', RT[page].bytes)

    @staticmethod
    def print_xelatex_error(log_path: AbsolutePath):
        with log_path.open(encoding='utf-8') as file:
            print('\033[1;31m', end='', file=sys.stderr)
            for line in file:
                line = line.rstrip()
                if line.startswith('! '):
                    print(line, file=sys.stderr)
                    break
            for line in file:
                line = line.rstrip()
                if line in ('End of file on the terminal!',
                            ' When in doubt, ask someone for help!',
                            'Here is how much of TeX\'s memory you used:',
                            '?'):
                    break
                print(line, file=sys.stderr)
            print('\033[0m', end='', file=sys.stderr)

    def make_internal_url(self, href: PageHref, *, page: Page = None) -> str:
        """
        Given a PageHref, i.e., a page and an optional anchor, generates a unique internal identifier for it.
        The function avoids using any non-ASCII characters, as well as the ``%`` character,
        so that the result can be used for PDF bookmarks.
        """
        if href.target.volume is not page.volume:
            raise DisableLink
        result = '--'.join(('r', *str(href.target.location).strip('/').split('/'))).rstrip('-')
        if href.anchor:
            result += '--' + href.anchor
        result = urllib.parse.quote(result).replace('%', '')
        result = '#' + result
        return result


class LatexProcessor(Processor[LatexBuilder]):

    @override
    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        r"""
        Generate LaTeX code based on the given `header`.

        The generated code includes:

        - the header content itself,
        - optional automatic numeration,
        - the \hypertarget and \bookmark tags for navigation.
        """
        # Run the default processing and make sure that the result is still a single Header
        header, = await super().process_header(header, page)
        assert isinstance(header, Header)

        header.identifier = urllib.parse.quote(header.identifier).replace('%', '')

        # Our result, however, will be not a Header, but a paragraph with custom LaTeX code.
        # We will generate inline elements into a list. In the end, we will wrap them all in a paragraph.
        result: list[Element] = []

        # Generate the internal link for \hyperref
        href = PageHref(page, header.identifier if header.level > 1 else None)
        dest = re.sub(r'^#', '', self.builder.make_internal_url(href, page=page))

        # Generate our hypertargets and bookmarks manually, to avoid any weird behavior with TOCs
        if 'notoc' not in header.classes:
            level = page.location.level + header.level - 1
            label = stringify(header).replace('%', r'\%')
            if page.volume.config.content.numeration:
                label = '%NUMBER%' + label
            result += LatexInline(fr'\bookmark[level={level},dest={dest}]{{{label}}}'), Str('\n')

        # Add the appropriate header tag and an opening curly bracket, e.g., '\section{'.
        tag = self.choose_header_tag(header, page)
        if 'notoc' in header.classes and tag[-1] != '*':
            tag += '*'
        result += LatexInline(fr'\{tag}{{'),

        # Put all the content of the original header here
        # For some reason, Pandoc does not escape `%` when it is a separate word,
        # so we escape it ourselves here
        if page.volume.config.content.numeration:
            result.append(LatexInline('%NUMBER%'))
        for item in header.content:
            if isinstance(item, Str) and item.text == '%':
                result.append(LatexInline(r'\%'))
            else:
                result.append(item)

        # Close the curly bracket
        result += LatexInline('}'), Str('\n')

        # Make it linkable for \hyperref
        result += LatexInline(fr'\label{{{dest}}}'),

        return (HeaderReplPara(header, result),)

    def choose_header_tag(self, header: Header, page: Page) -> str:
        config_headers: Config_Latex_Headers = page.volume.config.latex.headers

        for klass in header.classes:
            with suppress(KeyError):
                return config_headers.by_class[klass]

        with suppress(KeyError):
            return config_headers.by_global_level[page.location.level + header.level - 1]

        if header.level == 1:
            with suppress(KeyError):
                return config_headers.by_page_level[page.level]

        return config_headers.by_element[header.level]


@final
class LatexTheme(Theme, metaclass=ABCMeta):
    """
    A theme for LatexBuilder.

    It may or may not provide multiple files that will be included at the beginning of the resulting LaTeX document.
    """

    def __init__(self, theme_dir: AbsolutePath):
        super().__init__(theme_dir)

        def try_find_file(filename: str) -> AbsolutePath | None:
            path = theme_dir / filename
            if path.exists():
                return path
            return None

        self.style = try_find_file('style.sty')
        """LaTeX code to be included at the very beginning, even before ``\\begin{document}``."""

        self.cover = try_find_file('cover.tex')
        """LaTeX code to be included immediately after the document environment began."""

        self.toc = try_find_file('toc.tex')
        """LaTeX code to be included after the cover."""
