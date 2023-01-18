from asyncio import create_subprocess_exec
from io import StringIO
from pathlib import Path
from subprocess import PIPE

import panflute
from panflute import Doc

from sobiraka.building.processor import Processor
from sobiraka.utils import print_errors


class DocxBuilder(Processor):

    async def run(self, output: Path):
        output.parent.mkdir(parents=True, exist_ok=True)

        for page in self.book.pages:
            page.processed2.start()

        big_doc = Doc()
        for page in self.book.pages:
            await page.processed2.wait()
            big_doc.content.extend(page.doc.content)

        if print_errors(self.book):
            raise Exception

        with StringIO() as stringio:
            panflute.dump(big_doc, stringio)
            json_bytes = stringio.getvalue().encode('utf-8')

        pandoc = await create_subprocess_exec(
            'pandoc',
            '--from', 'json',
            '--to', 'docx',
            '--resource-path', self.book.root / '_images',
            '--output', output,
            stdin=PIPE)
        pandoc.stdin.write(json_bytes)
        pandoc.stdin.close()
        await pandoc.wait()
        assert pandoc.returncode == 0
