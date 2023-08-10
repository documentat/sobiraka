from panflute import Element, Header, Link, Space, Str

from sobiraka.models import Page
from sobiraka.processing.htmlbuilder import HtmlTheme


class Theme(HtmlTheme):
    async def process_header(self, elem: Header, page: Page) -> tuple[Element, ...]:
        if elem.level >= 2:
            elem.content += (Space(),
                             Link(Str('#'), url=f'#{elem.identifier}', classes=['anchor']))
        return (elem,)
