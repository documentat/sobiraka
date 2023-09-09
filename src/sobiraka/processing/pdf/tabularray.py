from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from panflute import BulletList, Element, LineBreak, Plain, Space, Str, Table, TableBody, TableCell, stringify

from sobiraka.models import Page
from sobiraka.utils import LatexBlock, LatexInline
from ..abstract import Dispatcher
from ..replacement import TableReplPara


class TabulArrayProcessor(Dispatcher):

    async def process_table(self, table: Table, page: Page) -> tuple[Element, ...]:
        table = await self.process_container(table, page)
        assert isinstance(table, Table)

        result = [TableReplPara(table)]

        result[-1].content.append(LatexInline(r'\begin{tblr}'
                                        + '[' + ','.join(self.tabularray_table_square_bracket_options(table)) + ']'
                                        + '{' + ','.join(self.tabularray_table_curly_bracket_options(table)) + '}'))
        result[-1].content.append(Str('\n'))

        assert len(table.head.content) == 1, 'This class does not support multi-row table heads yet.'
        head_row = table.head.content[0]
        for i, head_cell in enumerate(head_row.content):
            assert head_cell.colspan == 1, 'This class does not support multi-column cells yet.'
            result[-1].content += *head_cell.content[0].content, Space()
            if i < len(head_row.content) - 1:
                result[-1].content += LatexInline('&'), Str('\n')
        result[-1].content += Str('\n'), LatexInline('\\\\'), Str('\n')

        for i, row in enumerate(_grid(table)):
            do_not_break_table = False
            for j, grid_item in enumerate(row):
                match grid_item:
                    case CellPlacement() as cell_placement:
                        self._make_cell(cell_placement, table, result)
                        if cell_placement.cell.rowspan > 1:
                            do_not_break_table = True

                    case CellContinuation() as cell_continuation:
                        if not cell_continuation.is_last_row:
                            do_not_break_table = True

                if j == len(row) - 1:
                    if do_not_break_table:
                        result[-1].content += Str('\n'), LatexInline('\\\\*'), Str('\n')
                    else:
                        result[-1].content += Str('\n'), LatexInline('\\\\'), Str('\n')
                else:
                    result[-1].content += Space(), LatexInline('&'), Str('\n')

        result[-1].content.append(LatexInline(r'''
             \end{tblr}
        '''))

        return tuple(result)

    def _make_cell(self, cell_placement: CellPlacement, table: Table, result: list[TableReplPara]):
        cell = cell_placement.cell
        assert cell.colspan == 1, 'This class does not support multi-column cells yet.'

        cell_square_bracket_options = list(self.tabularray_cell_square_bracket_options(cell_placement))
        cell_curly_bracket_options = list(self.tabularray_cell_curly_bracket_options(cell_placement))
        if cell.rowspan > 1:
            cell_square_bracket_options.append(f'r={cell.rowspan}')
        if cell_square_bracket_options or cell_curly_bracket_options:
            set_cell = r'\SetCell'
            if cell_square_bracket_options:
                set_cell += '[' + ','.join(cell_square_bracket_options) + ']'
            set_cell += '{' + ','.join(cell_curly_bracket_options) + '}'
            result[-1].content += Space(), LatexInline(set_cell)

        result[-1].content += LatexInline('{'), Space()

        if len(cell.content) == 1 and isinstance(cell.content[0], Plain):
            for inline_item in cell.content[0].content:
                if isinstance(inline_item, LineBreak):
                    result[-1].content += Space(), LatexInline('\\\\'), Space()
                else:
                    result[-1].content.append(inline_item)

        else:
            result[-1].content += Str('\n'), LatexInline('% BEGIN STRIP')
            for block_item in cell.content:
                if isinstance(block_item, BulletList):
                    result += \
                        LatexBlock(r'\begin{tcolorbox}[size=tight,opacityframe=0,opacityback=0]'), \
                            block_item, \
                            LatexBlock(r'\end{tcolorbox}'), \
                            TableReplPara(table)
                else:
                    result.append(block_item)
                    result.append(TableReplPara(table))
            result[-1].content += LatexInline('% END STRIP'), Str('\n')

        result[-1].content += Space(), LatexInline('}')

    def tabularray_colspec(self, table: Table) -> Sequence[str]:
        return 'X' * table.cols

    def tabularray_table_square_bracket_options(self, table: Table) -> Sequence[str]:
        # pylint: disable=unused-argument
        yield 'long=true'
        yield 'theme=empty'

    def tabularray_table_curly_bracket_options(self, table: Table) -> Sequence[str]:
        yield 'colspec={' + ''.join(self.tabularray_colspec(table)) + '}'
        yield 'rowhead=1'
        yield 'cells={valign=t}'

    def tabularray_cell_square_bracket_options(self, cell_placement: CellPlacement) -> Sequence[str]:
        # pylint: disable=unused-argument
        return []

    def tabularray_cell_curly_bracket_options(self, cell_placement: CellPlacement) -> Sequence[str]:
        # pylint: disable=unused-argument
        return []


@dataclass
class CellPlacement:
    cell: TableCell | None
    i: int = None
    j: int = None
    counted_i: int = None
    counted_j: int = None

    def __repr__(self):
        return f'<PLACE({self.i},{self.j}) {repr(stringify(self.cell)[:20])}>'


@dataclass
class CellContinuation:
    original: CellPlacement
    i: int = None
    j: int = None

    def __repr__(self):
        return f'<CONTINUE({self.i},{self.j}) {repr(stringify(self.original.cell)[:20])}>'

    @property
    def is_last_row(self) -> bool:
        return self.i == self.original.i + self.original.cell.rowspan - 1


def _grid(table: Table) -> list[list[CellPlacement | CellContinuation]]:
    body: TableBody = table.content[0]
    rownum = len(body.content)
    colnum = table.cols
    grid: list[list[CellPlacement | CellContinuation | None]] = [[None for _ in range(colnum)] for _ in range(rownum)]

    for i in range(rownum):
        iter_source = iter(table.content[0].content[i].content)
        for j in range(colnum):
            if grid[i][j] is None:
                cell: TableCell = next(iter_source)
                grid[i][j] = CellPlacement(cell)
                for continuation_i in range(i + 1, i + cell.rowspan):
                    grid[continuation_i][j] = CellContinuation(grid[i][j])

    for i in range(rownum):
        for j in range(colnum):
            grid[i][j].i = i
            grid[i][j].j = j

    for i in range(rownum):
        counted_j = 0
        for j in range(colnum):
            if isinstance(grid[i][j], CellPlacement):
                grid[i][j].counted_j = counted_j
                counted_j += 1
    for j in range(colnum):
        counted_i = 0
        for i in range(rownum):
            if isinstance(grid[i][j], CellPlacement):
                grid[i][j].counted_i = counted_i
                counted_i += 1

    return grid
