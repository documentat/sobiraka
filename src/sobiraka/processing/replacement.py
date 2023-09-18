from typing import Generic, Iterable, TypeVar

from panflute import Block, CodeBlock, Header, Inline, Para, Table

T = TypeVar('T', bound=Block)


class _ReplPara(Para, Generic[T]):
    tag = 'Para'

    def __init__(self, original_elem: T, items: Iterable[Inline] = ()):
        super().__init__(*items)
        self.original_elem: T = original_elem


class CodeReplPara(_ReplPara[CodeBlock]):
    """An auto-generated paragraph that replaces or wraps a code block."""


class HeaderReplPara(_ReplPara[Header]):
    """An auto-generated paragraph that replaces or wraps a Header."""


class TableReplPara(_ReplPara[Table]):
    """An auto-generated paragraph that replaces or wraps a Table."""
