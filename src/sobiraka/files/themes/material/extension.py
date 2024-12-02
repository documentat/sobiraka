from uuid import uuid4

import yattag
from panflute import CodeBlock, Div, Element, Header, Link, RawBlock, Space, Str
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name
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

    @override
    async def process_code_block(self, block: CodeBlock, page: Page) -> tuple[Element, ...]:
        block, = await super().process_code_block(block, page)
        assert isinstance(block, CodeBlock)

        syntax, = block.classes or ('text',)
        pygments_lexer = get_lexer_by_name(syntax)
        pygments_formatter = HtmlFormatter(nowrap=True)
        pygments_output = highlight(block.text, pygments_lexer, pygments_formatter)

        code_block_id = f'code-{uuid4()}'

        html = yattag.Doc()
        with html.tag('div', klass=f'highlight-{syntax} notranslate'):
            with html.tag('div', klass='highlight'):
                with html.tag('pre', id=code_block_id):
                    html.asis(pygments_output)

        result = RawBlock(html.getvalue())
        return (result,)

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
