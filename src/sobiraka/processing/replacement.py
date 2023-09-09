from typing import Generic, TypeVar

from panflute import Block, Header, Para, Table

T = TypeVar('T', bound=Block)


class _ReplPara(Para, Generic[T]):
    tag = 'Para'

    def __init__(self, original_elem: T, *args):
        super().__init__(*args)
        self.original_elem: T = original_elem


class HeaderReplPara(_ReplPara[Header]):
    """An auto-generated paragraph that replaces or wraps a Header."""


class TableReplPara(_ReplPara[Table]):
    """An auto-generated paragraph that replaces or wraps a Table."""
