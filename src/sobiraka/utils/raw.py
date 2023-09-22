from textwrap import dedent

from panflute import RawBlock, RawInline


class HtmlBlock(RawBlock):
    tag = 'RawBlock'

    def __init__(self, text: str):
        super().__init__(dedent(text).strip(), 'html')


class HtmlInline(RawInline):
    tag = 'RawInline'

    def __init__(self, text: str):
        super().__init__(dedent(text).strip(), 'html')



class LatexBlock(RawBlock):
    tag = 'RawBlock'

    def __init__(self, text: str):
        super().__init__(dedent(text).strip(), 'latex')


class LatexInline(RawInline):
    tag = 'RawInline'

    def __init__(self, text: str):
        super().__init__(dedent(text).strip(), 'latex')
