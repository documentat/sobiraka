from asyncio import create_subprocess_exec
from subprocess import PIPE

from panflute import BulletList, Element, Image, Plain, Str, Table, TableBody, TableCell, TableHead

from sobiraka.models import Page
from sobiraka.utils import panflute_to_bytes
from .processor import Processor


class Plainifier(Processor):

    async def plainify(self, page: Page) -> str:
        await self.process2(page)

        pandoc = await create_subprocess_exec(
            'pandoc',
            '--from', 'json',
            '--to', 'plain',
            '--wrap', 'none',
            stdin=PIPE,
            stdout=PIPE)
        pandoc.stdin.write(panflute_to_bytes(self.doc[page]))
        pandoc.stdin.close()
        await pandoc.wait()
        assert pandoc.returncode == 0

        result = await pandoc.stdout.read()
        return result.decode('utf-8')

    ################################################################################

    async def process_bullet_list(self, elem: BulletList, page: Page) -> tuple[Element, ...]:
        result: list[Element] = []

        for item in elem.content.list:
            for item_content in item.content.list:
                match item_content:
                    case Plain() as plain:
                        result.extend(await self.process_plain(plain, page))
                    case BulletList() as sublist:
                        result.extend(await self.process_bullet_list(sublist, page))
                    case _:
                        raise TypeError(type(item_content))

        return tuple(result)

    async def process_image(self, elem: Image, page: Page):
        return Str(elem.title)

    async def process_table(self, elem: Table, page: Page):
        result: list[Element] = []

        assert isinstance(head := elem.head, TableHead)
        assert len(elem.content) == 1
        assert isinstance(body := elem.content[0], TableBody)

        for row in head.content.list + body.content.list:
            for cell in row.content:
                result += cell.content.list

        return tuple(result)

    async def process_table_cell(self, elem: TableCell, page: Page):
        return tuple(elem.content.list)
