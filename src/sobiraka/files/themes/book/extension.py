from panflute import Div, Element, Header, Link, RawBlock, Space, Str
from typing_extensions import override

from sobiraka.models import Page, Status
from sobiraka.processing.web import WebProcessor
from sobiraka.runtime import RT


class BookThemeProcessor(WebProcessor):
    """
    A clean and simple HTML theme, based on https://github.com/alex-shpak/hugo-book.
    Supports multilanguage projects.
    """

    @override
    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        header, = await super().process_header(header, page)
        assert isinstance(header, Header)

        if header.level >= 2:
            header.content += Space(), Link(Str('#'), url=f'#{header.identifier}', classes=['anchor'])

        self.builder.waiter.add_task(self.numerate_header(header, page))

        return header,

    async def process_div_note(self, div: Div, page: Page) -> tuple[Element, ...]:
        div, = await super().process_div(div, page)
        assert isinstance(div, Div)

        return (RawBlock('<blockquote class="book-hint info">'),
                *div.content,
                RawBlock('</blockquote>'))

    async def process_div_example(self, div: Div, page: Page) -> tuple[Element, ...]:
        div, = await super().process_div(div, page)
        assert isinstance(div, Div)

        return (RawBlock('<blockquote class="book-hint example">'),
                *div.content,
                RawBlock('</blockquote>'))

    async def process_div_warning(self, div: Div, page: Page) -> tuple[Element, ...]:
        div, = await super().process_div(div, page)
        assert isinstance(div, Div)

        return (RawBlock('<blockquote class="book-hint warning">'),
                *div.content,
                RawBlock('</blockquote>'))

    async def process_div_danger(self, div: Div, page: Page) -> tuple[Element, ...]:
        div, = await super().process_div(div, page)
        assert isinstance(div, Div)

        return (RawBlock('<blockquote class="book-hint danger">'),
                *div.content,
                RawBlock('</blockquote>'))

    async def numerate_header(self, header: Header, page: Page):
        await self.builder.waiter.wait(page, Status.PROCESS3)

        if header.level == 1:
            header.content = Str(RT[page].number.format('{}. ')), *header.content
        else:
            anchor = RT[page].anchors.by_header(header)
            header.content = Str(RT[anchor].number.format('{}. ')), *header.content
