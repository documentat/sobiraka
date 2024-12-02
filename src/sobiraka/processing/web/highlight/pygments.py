from typing import Iterable, TYPE_CHECKING

import yattag
from panflute import Block, CodeBlock, RawBlock
from typing_extensions import override

from sobiraka.models.config import Config_Pygments
from sobiraka.utils import RelativePath
from .abstract import Highlighter
from ..head import HeadCssFile, HeadTag

if TYPE_CHECKING:
    from sobiraka.processing.web import AbstractHtmlBuilder


class Pygments(Highlighter):
    """
    Website: https://pygments.org/
    """
    def __init__(self, config: Config_Pygments, builder: 'AbstractHtmlBuilder'):
        from pygments.formatters.html import HtmlFormatter
        from pygments.styles import get_style_by_name

        super().__init__()
        self.config: Config_Pygments = config
        self.builder: AbstractHtmlBuilder = builder

        self.formatter: HtmlFormatter
        self.head: list[HeadCssFile] = []

        # If a style is selected, use Pygments to generate the corresponding CSS code
        if config.style is not None:
            pygments_style = get_style_by_name(config.style)
            self.formatter = HtmlFormatter(nowrap=True, wrapcode=True, style=pygments_style)
            style_path = RelativePath() / '_static' / 'css' / f'pygments-{config.style}.css'
            builder.add_file_from_data(style_path, self.formatter.get_style_defs('pre code.pygments'))
            self.head.append(HeadCssFile(style_path))
        else:
            self.formatter = HtmlFormatter(nowrap=True, wrapcode=True)

    @override
    def highlight(self, block: CodeBlock) -> tuple[Block, Iterable[HeadTag]]:
        from pygments.lexers import get_lexer_by_name
        from pygments import highlight

        language = block.classes[0] if len(block.classes) > 0 else 'text'
        lexer = get_lexer_by_name(language)
        output = highlight(block.text, lexer, self.formatter).rstrip()

        pre_attributes = dict(klass=self.config.pre_class) if self.config.pre_class else {}
        code_attributes = dict(klass=self.config.code_class) if self.config.code_class else {}

        html = yattag.Doc()
        with html.tag('pre', **pre_attributes):
            with html.tag('code', **code_attributes):
                html.asis(output)
        block = RawBlock(html.getvalue())

        return block, self.head
