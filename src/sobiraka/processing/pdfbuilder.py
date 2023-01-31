import sys
from asyncio import create_subprocess_exec
from pathlib import Path
from shutil import copyfile
from subprocess import DEVNULL, PIPE
from typing import BinaryIO

from sobiraka.models import Book, Page
from sobiraka.runtime import RT
from sobiraka.utils import on_demand, panflute_to_bytes
from .abstract import Processor


class PdfBuilder(Processor):
    def __init__(self, book: Book):
        super().__init__(book)
        self._latex: dict[Page, bytes] = {}

    async def run(self, output: Path):
        output.parent.mkdir(parents=True, exist_ok=True)

        xelatex_workdir = RT.TMP / f'tex-{self.book.id}'
        xelatex_workdir.mkdir(parents=True, exist_ok=True)
        for item in xelatex_workdir.iterdir():
            if item.is_dir():
                item.rmdir()
            else:
                item.unlink()

        with open(xelatex_workdir / 'build.tex', 'wb') as latex_output:
            await self.generate_latex(latex_output)

        xelatex = await create_subprocess_exec(
            'xelatex',
            'build.tex',
            '-halt-on-error',
            cwd=xelatex_workdir,
            stdin=DEVNULL,
            stdout=DEVNULL)
        await xelatex.wait()
        if xelatex.returncode != 0:
            self.print_xelatex_error(xelatex_workdir / 'build.log')
            exit(1)
        copyfile(xelatex_workdir / 'build.pdf', output)

    async def generate_latex(self, latex_output: BinaryIO):
        for page in self.book.pages:
            hash(page.book)
            self.generate_latex_for_page(page).start()

        if self.print_errors():
            raise Exception

        latex_output.write((RT.FILES / 'base.sty').read_bytes())
        latex_output.write(b'\n\n' + (80 * b'%'))
        if self.book.pdf.header:
            latex_output.write(b'\n\n')
            latex_output.write(self.book.pdf.header.read_bytes())
            latex_output.write(b'\n\n' + (80 * b'%'))
        latex_output.write(b'\n\n\\begin{document}\n\\begin{sloppypar}')

        for page in self.book.pages:
            await self.generate_latex_for_page(page)
            latex_output.write(b'\n\n' + (80 * b'%'))
            latex_output.write(b'\n\n%%% ' + bytes(page.relative_path) + b'\n')
            latex_output.write(self._latex[page])

        latex_output.write(b'\n\n' + (80 * b'%'))
        latex_output.write(b'\n\n\\end{sloppypar}\n\\end{document}')

    @on_demand
    async def generate_latex_for_page(self, page: Page):
        await self.process2(page)

        if len(self.doc[page].content) == 0:
            self._latex[page] = b''

        else:
            pandoc = await create_subprocess_exec(
                'pandoc',
                '--from', 'json',
                '--to', 'latex-smart',
                '--resource-path', self.book.root / '_images',
                '--wrap', 'none',
                stdin=PIPE,
                stdout=PIPE)
            pandoc.stdin.write(panflute_to_bytes(self.doc[page]))
            pandoc.stdin.close()
            await pandoc.wait()
            assert pandoc.returncode == 0
            self._latex[page] = await pandoc.stdout.read()

        if RT.TMP:
            (RT.TMP / 'content' / page.relative_path.with_suffix('.tex')).write_bytes(self._latex[page])

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
                if line == 'End of file on the terminal!':
                    break
                print(line, file=sys.stderr)
            print('\033[0m', end='', file=sys.stderr)