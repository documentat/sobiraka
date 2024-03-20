from panflute import Div, Element, Header, Link, RawBlock, Space, Str

from sobiraka.models import Page
from sobiraka.processing.plugin import HtmlTheme


class BookTheme(HtmlTheme):
    """
    A clean and simple HTML theme, based on https://github.com/alex-shpak/hugo-book.
    Supports multilanguage projects.
    """
    # pylint: disable=unused-argument

    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        if header.level >= 2:
            header.content += (Space(),
                               Link(Str('#'), url=f'#{header.identifier}', classes=['anchor']))
        return (header,)

    async def process_div_note(self, div: Div, page: Page) -> tuple[Element, ...]:
        div, = await super().process_div(div, page)
        assert isinstance(div, Div)

        return (RawBlock('<blockquote class="book-hint info">'),
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
