from panflute import Code, CodeBlock, Element, Str

from sobiraka.models import Page
from sobiraka.utils import LatexInline
from ..abstract import Dispatcher
from ..replacement import CodeReplPara


class Minted(Dispatcher):
    """
    Use https://www.ctan.org/pkg/minted for block and inline code elements.
    """

    async def process_code_block(self, block: CodeBlock, page: Page) -> tuple[Element, ...]:
        source = block.text
        syntax = block.classes[0] if block.classes else 'text'
        para = CodeReplPara(block, (
            LatexInline(r'\begin{minted}{' + syntax + '}'),
            Str('\n'),
            LatexInline(source),
            Str('\n'),
            LatexInline(r'\end{minted}'),
        ))
        return (para,)

    async def process_code(self, code: Code, page: Page) -> tuple[Element, ...]:
        source = code.text
        return (LatexInline(r'\mintinline{text}{' + source + '}'),)
