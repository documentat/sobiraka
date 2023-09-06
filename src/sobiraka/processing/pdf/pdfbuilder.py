import os
import re
import sys
import urllib.parse
from asyncio import create_subprocess_exec, gather
from pathlib import Path
from shutil import copyfile
from subprocess import DEVNULL, PIPE
from typing import BinaryIO

from panflute import Element, Header, Space, Str, stringify

from sobiraka.models import Counter, Page, PageHref, Volume
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

        self._theme: PdfTheme | None = None
        if self.volume.config.pdf.theme is not None:
            self._theme = load_pdf_theme(self.volume.config.pdf.theme)

        self._numeration = Counter()

    async def run(self):
        self.output.parent.mkdir(parents=True, exist_ok=True)

        xelatex_workdir = RT.TMP / 'tex'
        xelatex_workdir.mkdir(parents=True, exist_ok=True)
        for item in xelatex_workdir.iterdir():
            if item.is_dir():
                item.rmdir()
            else:
                item.unlink()

        with open(xelatex_workdir / 'build.tex', 'wb') as latex_output:
            await self.generate_latex(latex_output)

        env = os.environ | {'TEXINPUTS': f'{self.volume.project.fs.resolve(self.volume.config.paths.resources)}:'}
        for n in range(1, 4):
            print(f'Running XeLaTeX ({n})...', file=sys.stderr)
            xelatex = await create_subprocess_exec(
                'xelatex',
                'build.tex',
                '-halt-on-error',
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

        if self._theme.style is not None:
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% ' + self._theme.__class__.__name__.encode('utf-8') + b'\n\n')
            latex_output.write(self._theme.style.read_bytes())
            latex_output.write(b'\n\n' + (80 * b'%'))
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

        if self._theme is not None:
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
        result = href.target.id
        if href.anchor:
            result += '--' + href.anchor
        result = urllib.parse.quote(result).replace('%', '')
        return result

    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        header, = await super().process_header(header, page)
        assert isinstance(header, Header)

        volume: Volume = page.volume
        config = page.volume.config

        if config.pdf.numeration:
            # Wait until all previous pages are processed
            n = volume.pages.index(page)
            await gather(*map(self.process1, volume.pages[:n]))

            # Increase the numeration counter and print it
            self._numeration.increase(header.level)
            header.content = Str(f'{self._numeration}.'), Space(), *header.content

        latex: list[Element] = []

        dest = self.make_internal_url(PageHref(page, header.identifier if header.level > 1 else None), page=page)
        latex += LatexInline(fr'\hypertarget{{{dest}}}{{}}'), Str('\n')
        latex += LatexInline(fr'\bookmark[level={header.level},dest={dest}]{{ {stringify(header)} }}'), Str('\n')

        tag = {
            1: 'section',
            2: 'subsection',
            3: 'subsubsection',
            4: 'paragraph',
            5: 'subparagraph',
        }[header.level]
        latex += LatexInline(fr'\{tag}{{'), Space()

        latex += header.content

        latex += Space(), LatexInline('}')

        return (HeaderReplPara(header, *latex),)
