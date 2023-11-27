import os
import re
import sys
import urllib.parse
from asyncio import create_subprocess_exec
from pathlib import Path
from shutil import copyfile
from subprocess import DEVNULL, PIPE
from types import NoneType
from typing import BinaryIO

from panflute import Element, Header, Space, Str, stringify

from sobiraka.cache import CACHE
from sobiraka.models import Page, PageHref, Volume
from sobiraka.models.exceptions import DisableLink
from sobiraka.runtime import RT
from sobiraka.utils import LatexInline, on_demand, panflute_to_bytes
from ..abstract import VolumeProcessor
from ..plugin import PdfTheme, load_pdf_theme
from ..replacement import HeaderReplPara


class PdfBuilder(VolumeProcessor):
    def __init__(self, volume: Volume, output: Path):
        super().__init__(volume)
        self.output: Path = output

        self._latex: dict[Page, bytes] = {}

        # Load an optional post-processor a.k.a. PdfTheme
        self._theme: PdfTheme | None = None
        if self.volume.config.pdf.theme is not None:
            self._theme = load_pdf_theme(self.volume.config.pdf.theme)

    async def run(self):
        xelatex_workdir = RT.TMP / 'tex'
        xelatex_workdir.mkdir(parents=True, exist_ok=True)

        with open(xelatex_workdir / 'build.tex', 'wb') as latex_output:
            await self.generate_latex(latex_output)

        resources_dir = self.volume.project.fs.resolve(self.volume.config.paths.resources)
        for n in range(1, 4):
            print(f'Running XeLaTeX ({n})...', file=sys.stderr)
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
                sys.exit(1)

        self.output.parent.mkdir(parents=True, exist_ok=True)
        copyfile(xelatex_workdir / 'build.pdf', self.output)

        return 0

    async def generate_latex(self, latex_output: BinaryIO):
        volume = self.volume
        project = self.volume.project
        config = self.volume.config

        for page in volume.pages:
            self.generate_latex_for_page(page).start()

        if self.print_issues():
            sys.exit(1)

        variables = {
            'TITLE': config.title,
            'LANG': volume.lang,
            **config.variables,
        }
        latex_output.write(b'\n\n' + (80 * b'%'))
        latex_output.write(b'\n\n%%% Variables\n\n')
        for key, value in variables.items():
            key = key.replace('_', '')
            latex_output.write(fr'\newcommand{{\{key}}}{{{value}}}'.encode('utf-8') + b'\n')

        if self._theme.style is not None:
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% ' + self._theme.__class__.__name__.encode('utf-8') + b'\n\n')
            latex_output.write(self._theme.style.read_bytes())

        if config.pdf.header:
            latex_output.write(b'\n\n')
            latex_output.write(b'\n\n%%% Project\'s custom header \n\n')
            latex_output.write(project.fs.read_bytes(config.pdf.header))

        latex_output.write(b'\n\n' + (80 * b'%'))
        latex_output.write(b'\n\n\\begin{document}\n\\begin{sloppypar}')

        if self._theme.cover is not None:
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% Cover\n\n')
            latex_output.write(self._theme.cover.read_bytes())

        if config.pdf.toc and self._theme.toc is not None:
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% Table of contents\n\n')
            latex_output.write(self._theme.toc.read_bytes())

        for page in volume.pages:
            await self.generate_latex_for_page(page)
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% ' + bytes(page.path_in_project) + b'\n\n')
            latex_output.write(RT[page].latex)

        latex_output.write(b'\n\n' + (80 * b'%'))
        latex_output.write(b'\n\n\\end{sloppypar}\n\\end{document}')

    @on_demand
    async def generate_latex_for_page(self, page: Page):
        try:
            RT[page].dependencies = CACHE[page].get_dependencies()
        except KeyError:
            await self.process1(page)

        try:
            RT[page].latex = CACHE[page].get_latex(RT[page].dependencies)
            return
        except KeyError:
            pass
        await self.process2(page)

        # If a theme is set, run additional processing of the whole document
        # Note that if the theme does not contain custom logic implementation, we skip this step as useless
        if type(self._theme) not in (NoneType, PdfTheme):
            await self._theme.process_doc(RT[page].doc, page)

        if len(RT[page].doc.content) == 0:
            RT[page].latex = b''

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
            RT[page].latex = await pandoc.stdout.read()

            # When a PdfTheme prepends or appends some code to a Para,
            # it may leave the 'BEGIN STRIP'/'END STRIP' notes,
            # which we will now use to remove unnecessary empty lines
            RT[page].latex = re.sub(rb'% BEGIN STRIP\n+', b'', RT[page].latex)
            RT[page].latex = re.sub(rb'\n+% END STRIP', b'', RT[page].latex)

        CACHE[page].set_latex(RT[page])

    @staticmethod
    def print_xelatex_error(log_path: Path):
        with log_path.open() as file:
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

    def make_internal_url(self, href: PageHref, *, page: Page) -> str:
        """
        Given a PageHref, i.e., a page and an optional anchor, generates a unique internal identifier for it.
        The function avoids using any non-ASCII characters, as well as the ``%`` character,
        so that the result can be used for PDF bookmarks.
        """
        if href.target.volume is not page.volume:
            raise DisableLink
        result = href.target.id
        if href.anchor:
            result += '--' + href.anchor
        result = urllib.parse.quote(result).replace('%', '')
        result = '#' + result
        return result

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

        # Our result, however, will be not a Header, but a paragraph with custom LaTeX code.
        # We will generate inline elements into a list. In the end, we will wrap them all in a paragraph.
        result: list[Element] = []

        # Generate our hypertargets and bookmarks manually, to avoid any weird behavior with TOCs
        if 'notoc' not in header.classes:
            href = PageHref(page, header.identifier if header.level > 1 else None)
            dest = re.sub(r'^#', '', self.make_internal_url(href, page=page))
            label = stringify(header).replace('%', r'\%')
            result += LatexInline(fr'\hypertarget{{{dest}}}{{}}'), Str('\n')
            result += LatexInline(fr'\bookmark[level={header.level},dest={dest}]{{ {label} }}'), Str('\n')

        # Add the appropriate header tag and an opening curly bracket, e.g., '\section{'.
        tag = {
            1: 'section',
            2: 'subsection',
            3: 'subsubsection',
            4: 'paragraph',
            5: 'subparagraph',
        }[header.level]
        if 'notoc' in header.classes:
            tag += '*'
        result += LatexInline(fr'\{tag}{{'), Space()

        # Put all the content of the original header here
        # For some reason, Pandoc does not escape `%` when it is a separate word,
        # so we escape it ourselves here
        for item in header.content:
            if isinstance(item, Str) and item.text == '%':
                result.append(LatexInline(r'\%'))
            else:
                result.append(item)

        # Close the curly bracket
        result += Space(), LatexInline('}')

        return (HeaderReplPara(header, result),)
