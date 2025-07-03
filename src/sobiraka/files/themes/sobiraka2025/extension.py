from abc import ABCMeta
from asyncio import create_task

import PIL.Image
from panflute import Caption, Div, Element, Figure, Header, Image, Link, Para, Plain, Space, Str, Table
from typing_extensions import override

from sobiraka.models import Page, Status
from sobiraka.processing.html import AbstractHtmlProcessor
from sobiraka.processing.weasyprint import WeasyPrintProcessor
from sobiraka.processing.web import WebProcessor
from sobiraka.runtime import RT


class Sobiraka2025_Processor(AbstractHtmlProcessor, metaclass=ABCMeta):

    @override
    async def process_para(self, para: Para, page: Page) -> tuple[Element, ...]:
        para, = await super().process_para(para, page)
        assert isinstance(para, Para)

        if len(para.content) == 1 and isinstance(image := para.content[0], Image):
            image_path = page.volume.config.paths.resources / image.url

            if isinstance(self, WebProcessor):
                with page.project.fs.open_bytes(image_path) as image_file:
                    with PIL.Image.open(image_file) as pil:
                        image.attributes['width'] = str(pil.width)
                        image.attributes['height'] = str(pil.height)
                result = Link(image, url=image.url)
                RT[page].links_that_follow_images.append((image, result))
            else:
                result = image

            if image.content:
                return Figure(Plain(result), caption=Caption(Plain(*image.content))),

            return Div(Plain(result), classes=['big-image']),

        return para,


class Sobiraka2025_WebProcessor(Sobiraka2025_Processor, WebProcessor):

    @override
    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        header, = await super().process_header(header, page)
        assert isinstance(header, Header)

        if header.level >= 2:
            self.builder.process4_tasks[page].append(create_task(self._linkify_header(header, page)))

        return header,

    async def _linkify_header(self, header: Header, page: Page):
        await self.builder.waiter.wait(page, Status.PROCESS3)

        header.content += Space(), Link(Str('#'), url=f'#{header.identifier}', classes=['anchor'])

    @override
    async def process_table(self, table: Table, page: Page) -> tuple[Element, ...]:
        table, = await super().process_table(table, page)
        assert isinstance(table, Table)

        return Div(table, classes=['table-wrapper']),


class Sobiraka2025_WeasyPrintProcessor(Sobiraka2025_Processor, WeasyPrintProcessor):
    pass
