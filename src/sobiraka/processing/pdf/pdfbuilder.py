import os
import re
import sys
import urllib.parse
from asyncio import create_subprocess_exec, gather
from pathlib import Path
from shutil import copyfile, rmtree
from subprocess import DEVNULL, PIPE
from types import NoneType
from typing import BinaryIO

from panflute import Element, Header, Space, Str, stringify

from sobiraka.models import Counter, Page, PageHref, Volume
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

        # Initialize a counter if we will need to numerate headers
        if self.volume.config.pdf.numeration:
            self._numeration = Counter()

    async def run(self):
        self.output.parent.mkdir(parents=True, exist_ok=True)

        xelatex_workdir = RT.TMP / 'tex'
        xelatex_workdir.mkdir(parents=True, exist_ok=True)
        for item in xelatex_workdir.iterdir():
            if item.is_dir():
                rmtree(item)
            else:
                item.unlink()

        with open(xelatex_workdir / 'build.tex', 'wb') as latex_output:
            await self.generate_latex(latex_output)

        env = os.environ | {'TEXINPUTS': f'{self.volume.project.fs.resolve(self.volume.config.paths.resources)}:'}
        for n in range(1, 4):
            print(f'Running XeLaTeX ({n})...', file=sys.stderr)
            xelatex = await create_subprocess_exec(
                'xelatex',
                '-shell-escape',
                '-halt-on-error',
                'build.tex',
                cwd=xelatex_workdir,
                env=env,
                stdin=DEVNULL,
                stdout=DEVNULL)
            await xelatex.wait()
            if xelatex.returncode != 0:
                self.print_xelatex_error(xelatex_workdir / 'build.log')
                sys.exit(1)
        copyfile(xelatex_workdir / 'build.pdf', self.output)

    async def generate_latex(self, latex_output: BinaryIO):
        volume = self.volume
        project = self.volume.project

        for page in volume.pages:
            self.generate_latex_for_page(page).start()

        if self.print_issues():
            sys.exit(1)

        variables = {
            'TITLE': volume.config.title,
            'LANG': volume.lang,
            **volume.config.variables,
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

        if volume.config.pdf.header:
            latex_output.write(b'\n\n')
            latex_output.write(b'\n\n%%% Project\'s custom header \n\n')
            latex_output.write(project.fs.read_bytes(volume.config.pdf.header))

        latex_output.write(b'\n\n' + (80 * b'%'))
        latex_output.write(b'\n\n\\begin{document}\n\\begin{sloppypar}')

        if self._theme.cover is not None:
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% cover\n\n')
            latex_output.write(self._theme.cover.read_bytes())

        if self._theme.toc is not None:
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% cover\n\n')
            latex_output.write(self._theme.toc.read_bytes())

        for page in volume.pages:
            await self.generate_latex_for_page(page)
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% ' + bytes(page.path_in_project) + b'\n\n')
            latex_output.write(self._latex[page])

        latex_output.write(b'\n\n' + (80 * b'%'))
        latex_output.write(b'\n\n\\end{sloppypar}\n\\end{document}')

    @on_demand
    async def generate_latex_for_page(self, page: Page):
        await self.process2(page)

        # If a theme is set, run additional processing of the whole document
        # Note that if the theme does not contain custom logic implementation, we skip this step as useless
        if type(self._theme) not in (NoneType, PdfTheme):
            await self._theme.process_container(self.doc[page], page)

        if len(self.doc[page].content) == 0:
            self._latex[page] = b''

        else:
            pandoc = await create_subprocess_exec(
                'pandoc',
                '--from', 'json',
                '--to', 'latex-smart',
                '--wrap', 'none',
                stdin=PIPE,
                stdout=PIPE)
            pandoc.stdin.write(panflute_to_bytes(self.doc[page]))
            pandoc.stdin.close()
            await pandoc.wait()
            assert pandoc.returncode == 0
            self._latex[page] = await pandoc.stdout.read()

            # When a PdfTheme prepends or appends some code to a Para,
            # it may leave the 'BEGIN STRIP'/'END STRIP' notes,
            # which we will now use to remove unnecessary empty lines
            self._latex[page] = re.sub(rb'% BEGIN STRIP\n+', b'', self._latex[page])
            self._latex[page] = re.sub(rb'\n+% END STRIP', b'', self._latex[page])

        if RT.TMP:
            (RT.TMP / 'content' / page.path_in_project.with_suffix('.tex')).write_bytes(self._latex[page])

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
        return result

    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        r"""
        Generate LaTeX code based on the given `header`.

        The generated code includes:

        - the header content itself,
        - optional automatic numeration,
        - the \hypertarget and \bookmark tags for navigation.
        """
        volume: Volume = page.volume
        config = page.volume.config

        # Run the default processing and make sure that the result is still a single Header
        header, = await super().process_header(header, page)
        assert isinstance(header, Header)

        # Our result, however, will be not a Header, but a paragraph with custom LaTeX code.
        # We will generate inline elements into a list. In the end, we will wrap them all in a paragraph.
        result: list[Element] = []

        # If we need to add numbers before each header in the document,
        # we wait until all previous pages (i.e. the pages that may affect the current page's numbering) are processed,
        # then we prepend the header with the number generated by a Counter object.
        # This feature respects the Pandoc's 'unnumbered' class (i.e., headers ending with '{-}').
        # The Counter object is initialized in the PdfBuilder.__init__() and is then used across all pages.
        if config.pdf.numeration:
            if 'unnumbered' not in header.classes:
                n = volume.pages.index(page)
                await gather(*map(self.process1, volume.pages[:n]))

                self._numeration.increase(header.level)
                header.content = Str(f'{self._numeration}.'), Space(), *header.content

        # Generate our hypertargets and bookmarks manually, to avoid any weird behavior with TOCs
        if 'notoc' not in header.classes:
            href = PageHref(page, header.identifier if header.level > 1 else None)
            dest = self.make_internal_url(href, page=page)
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
