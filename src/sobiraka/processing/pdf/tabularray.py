from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from panflute import BulletList, Element, LineBreak, Plain, Space, Str, Table, TableBody, TableCell, stringify

from sobiraka.models import Page
from sobiraka.utils import LatexBlock, LatexInline
from ..abstract import Dispatcher
from ..replacement import TableReplPara


class TabulArrayProcessor(Dispatcher):
    """
    For each Table element, generate custom LaTeX code that uses https://www.ctan.org/pkg/tabularray.
    Concrete options for tables and cells can be overriden using the tabularray_*() functions.

    Important: this class must be specified earlier than PdfTheme in the list of bases,
    otherwise Python will never choose the correct process_table().

    Here's a correct example:

        class MyPdfTheme(TabulArrayProcessor, PdfTheme):
            ...
    """

    async def process_table(self, table: Table, page: Page) -> tuple[Element, ...]:
        table, = await super().process_table(table, page)
        assert isinstance(table, Table)

        # This is where we will put all the content
        # Note that _make_cell() may or may not start a new Para, so it is highly recommended
        # that all other code here works with result[-1] without creating any aliases for the latest Para
        result = [TableReplPara(table)]

        # Begin the tblr environment
        # Let the user override both the square-bracket options and curly-bracket options for the table
        result[-1].content.append(LatexInline(
            r'\begin{tblr}'
            + '[' + ','.join(self.tabularray_table_square_bracket_options(table)) + ']'
            + '{' + ','.join(self.tabularray_table_curly_bracket_options(table)) + '}'))
        result[-1].content.append(Str('\n'))

        # Process table head
        assert len(table.head.content) == 1, 'This class does not support multi-row table heads yet.'
        head_row = table.head.content[0]
        for i, head_cell in enumerate(head_row.content):
            assert head_cell.colspan == 1, 'This class does not support multi-column cells yet.'
            result[-1].content += *head_cell.content[0].content, Space()
            if i < len(head_row.content) - 1:
                result[-1].content += LatexInline('&'), Str('\n')
        result[-1].content += Str('\n'), LatexInline('\\\\'), Str('\n')

        # Process table body
        # We use the _grid() function's results for iteration, which means that the coordinates (i, j)
        # always reflect where are we located “geometrically”, regardless of rowspans
        for i, row in enumerate(_grid(table)):
            do_not_break_table = False
            for j, grid_item in enumerate(row):
                match grid_item:
                    # When a new real cell begins, we call _make_cell() to write its content
                    # If this cell will be coninued in further rows, we forbid LaTeX from breaking page now
                    case CellPlacement() as cell_placement:
                        self._make_cell(cell_placement, table, result)
                        if cell_placement.cell.rowspan > 1:
                            do_not_break_table = True

                    # When a cell continues, we do not write anything, thus creating an empty placeholder
                    # If this is not the last row of a row-spanned cell, we forbid LaTeX from breaking page now
                    case CellContinuation() as cell_continuation:
                        if not cell_continuation.is_last_row:
                            do_not_break_table = True

                # If this is not the last cell in a row, write `&` after its content
                # For the last cell in a row, write `\\` (normally) or `\\*` (to forbid page break)
                if j < len(row) - 1:
                    result[-1].content += Space(), LatexInline('&'), Str('\n')
                else:
                    if do_not_break_table:
                        result[-1].content += Str('\n'), LatexInline('\\\\*'), Str('\n')
                    else:
                        result[-1].content += Str('\n'), LatexInline('\\\\'), Str('\n')

        # End the tblr environment
        result[-1].content.append(LatexInline(r'\end{tblr}'))

        return tuple(result)

    def _make_cell(self, cell_placement: CellPlacement, table: Table, result: list[TableReplPara]):
        cell = cell_placement.cell
        assert cell.colspan == 1, 'This class does not support multi-column cells yet.'

        # Write the \SetCell command and open the bracket for the cell content
        # Let the user override both the square-bracket options and curly-bracket options for the cell
        cell_square_bracket_options = list(self.tabularray_cell_square_bracket_options(cell_placement))
        cell_curly_bracket_options = list(self.tabularray_cell_curly_bracket_options(cell_placement))
        if cell.rowspan > 1:
            cell_square_bracket_options.append(f'r={cell.rowspan}')
        if cell_square_bracket_options or cell_curly_bracket_options:
            result[-1].content += Space(), LatexInline(
                r'\SetCell'
                + ('[' + ','.join(cell_square_bracket_options) + ']' if cell_square_bracket_options else '')
                + '{' + ','.join(cell_curly_bracket_options) + '}'
                + '{'), Space()

        # Check whether the cell's content is a plain element or a block
        if len(cell.content) == 1 and isinstance(cell.content[0], Plain):
            # For a plain element, copy all items as is, except for line breaks
            # Each line break inside the cell is replaced with `\\`
            for inline_item in cell.content[0].content:
                if isinstance(inline_item, LineBreak):
                    result[-1].content += Space(), LatexInline('\\\\'), Space()
                else:
                    result[-1].content.append(inline_item)

        else:
            # For a block element, we have to pause the table creation
            # and let Pandoc generate a whole paragraph as if it was separate.
            # We surround it with the 'BEGIN STRIP'/'END STRIP' notes,
            # which will be later processed by PdfBuilder to remove unnecessary newlines.
            # From the LaTeX point of view, the content is wrapped into a no-background `tcolorbox`.
            # Note that after this operation `result[-1]` points to a new Para.
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

        # Close the bracket for the cell content
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
    """
    A wrapper for `cell` that knows both its “geometric” position in the grid (`i`, `j`)
    and its “counted” position (`counted_i`, `counted_j`).
    """
    cell: TableCell | None

    i: int = None
    j: int = None

    counted_i: int = None
    counted_j: int = None

    def __repr__(self):
        return f'<PLACE({self.i},{self.j}) {repr(stringify(self.cell)[:20])}>'


@dataclass
class CellContinuation:
    """
    An item at a given “geometric” position (`i`, `j`) that does not provide any new content,
    but instead just holds place for a row-spanned `original`.
    """
    original: CellPlacement

    i: int = None
    j: int = None

    def __repr__(self):
        return f'<CONTINUE({self.i},{self.j}) {repr(stringify(self.original.cell)[:20])}>'

    @property
    def is_last_row(self) -> bool:
        return self.i == self.original.i + self.original.cell.rowspan - 1


def _grid(table: Table) -> list[list[CellPlacement | CellContinuation]]:
    """
    Reads a table and returns a two-dimensional array, in which
    there is either a CellPlacement or a CellContinuation for each possible position.
    Each element's `i` and `j` are set to the same values as its position in the array.

    The first coordinate is the row number, the second coordinate is the column number.

    The code assumes that `table.cols` (provided by panflute) is correct.
    """
    body: TableBody = table.content[0]
    rownum = len(body.content)
    colnum = table.cols
    grid: list[list[CellPlacement | CellContinuation | None]] \
        = [[None for _ in range(colnum)] for _ in range(rownum)]

    # Iterate through table cells
    for i in range(rownum):
        iter_source = iter(table.content[0].content[i].content)
        for j in range(colnum):
            # Skip adding a new item if this place is already taken
            if grid[i][j] is not None:
                continue

            # Take the next cell and put it into current location in grid
            cell: TableCell = next(iter_source)
            grid[i][j] = CellPlacement(cell)

            # For a row-spanned cell, generate continuations for locations below current
            for continuation_i in range(i + 1, i + cell.rowspan):
                grid[continuation_i][j] = CellContinuation(grid[i][j])

    # Set correct coordinates (i, j) for each grid item
    for i in range(rownum):
        for j in range(colnum):
            grid[i][j].i = i
            grid[i][j].j = j

    # Set correct “counted” coordinates (counted_i, counted_j) for each frid item
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
