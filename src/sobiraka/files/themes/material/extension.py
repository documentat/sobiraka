from panflute import Div, Element, Header, Link, RawBlock, Space, Str
from typing_extensions import override

from sobiraka.models import Page
from sobiraka.processing.web import WebProcessor


class MaterialThemeProcessor(WebProcessor):
    """
    Material-inspired HTML theme, based on https://bashtage.github.io/sphinx-material/.
    Support multilanguage projects.
    Supports some configuration options.
    """

    @override
    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        header, = await super().process_header(header, page)
        assert isinstance(header, Header)

        if header.level >= 2:
            header.content += (Space(),
                               Link(Str('¶'), url=f'#{header.identifier}', classes=['headerlink']))
        return (header,)

    async def process_div_note(self, div: Div, page: Page) -> tuple[Element, ...]:
        div, = await super().process_div(div, page)
        assert isinstance(div, Div)

        return (RawBlock('<div class="admonition note">'),
                RawBlock('<p class="admonition-title">Note</p>'),
                *div.content,
                RawBlock('</div>'))

    async def process_div_warning(self, div: Div, page: Page) -> tuple[Element, ...]:
        div, = await super().process_div(div, page)
        assert isinstance(div, Div)

        return (RawBlock('<div class="admonition warning">'),
                RawBlock('<p class="admonition-title">Warning</p>'),
                *div.content,
                RawBlock('</div>'))

    async def process_div_danger(self, div: Div, page: Page) -> tuple[Element, ...]:
        div, = await super().process_div(div, page)
        assert isinstance(div, Div)

        return (RawBlock('<div class="admonition danger">'),
                RawBlock('<p class="admonition-title">Danger</p>'),
                *div.content,
                RawBlock('</div>'))
