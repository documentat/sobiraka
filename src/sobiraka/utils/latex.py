from textwrap import dedent

from panflute import RawBlock, RawInline


class LatexBlock(RawBlock):
    tag = 'RawBlock'

    def __init__(self, text: str):
        super().__init__(dedent(text), 'latex')


class LatexInline(RawInline):
    tag = 'RawInline'

    def __init__(self, text: str):
        super().__init__(dedent(text), 'latex')
