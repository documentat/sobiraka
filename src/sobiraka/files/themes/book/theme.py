from panflute import Div, Element, Header, Link, RawBlock, Space, Str

from sobiraka.models import Page
from sobiraka.processing.plugin import HtmlTheme


class BookTheme(HtmlTheme):
    # pylint: disable=unused-argument

    async def process_header(self, elem: Header, page: Page) -> tuple[Element, ...]:
        if elem.level >= 2:
            elem.content += (Space(),
                             Link(Str('#'), url=f'#{elem.identifier}', classes=['anchor']))
        return (elem,)

    async def process_div_note(self, elem: Div, page: Page) -> tuple[Element, ...]:
        return (RawBlock('<blockquote class="book-hint info">'),
                *elem.content,
                RawBlock('</blockquote>'))

    async def process_div_warning(self, elem: Div, page: Page) -> tuple[Element, ...]:
        return (RawBlock('<blockquote class="book-hint warning">'),
                *elem.content,
                RawBlock('</blockquote>'))

    async def process_div_danger(self, elem: Div, page: Page) -> tuple[Element, ...]:
        return (RawBlock('<blockquote class="book-hint danger">'),
                *elem.content,
                RawBlock('</blockquote>'))
