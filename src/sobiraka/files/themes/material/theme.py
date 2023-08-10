from uuid import uuid4

import yattag
from panflute import CodeBlock, Element, Header, Link, RawBlock, Space, Str
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from sobiraka.models import Page
from sobiraka.processing.htmlbuilder import HtmlTheme


class MaterialTheme(HtmlTheme):
    async def process_header(self, elem: Header, page: Page) -> tuple[Element, ...]:
        if elem.level >= 2:
            elem.content += (Space(),
                             Link(Str('¶'), url=f'#{elem.identifier}', classes=['headerlink']))
        return (elem,)

    async def process_code_block(self, elem: CodeBlock, page: Page) -> tuple[Element, ...]:
        syntax, = elem.classes or ('text',)
        pygments_lexer = get_lexer_by_name(syntax)
        pygments_formatter = HtmlFormatter(nowrap=True)
        pygments_output = highlight(elem.text, pygments_lexer, pygments_formatter)

        code_block_id = f'code-{uuid4()}'

        html = yattag.Doc()
        with html.tag('div', klass=f'highlight-{syntax} notranslate'):
            with html.tag('div', klass='highlight'):
                with html.tag('pre', id=code_block_id):
                    html.asis(pygments_output)

        result = RawBlock(html.getvalue())
        return (result,)
