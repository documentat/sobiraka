from __future__ import annotations

from typing import Sequence

from panflute import BulletList, Element, LineBreak, Plain, Space, Str, Table

from sobiraka.models import Page
from sobiraka.utils import LatexBlock, LatexInline
from sobiraka.processing.abstract import Dispatcher
from sobiraka.processing.helpers.table import CellContinuation, CellPlacement, make_grid
from sobiraka.processing.replacement import TableReplPara


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

        # Process table body
        # We use the make_grid() function's results for iteration, which means that the coordinates (i, j)
        # always reflect where are we located “geometrically”, regardless of rowspans
        for row in make_grid(table):
            do_not_break_table = False
            for grid_item in row:
                match grid_item:
                    # When a new real cell begins, we call _make_cell() to write its content
                    # If this cell will be continued in further rows, we forbid LaTeX from breaking page now
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
                if grid_item.j < len(row) - 1:
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

        # Write the \SetCell[]{} command
        # Let the user override both the square-bracket options and curly-bracket options for the cell
        # Note that the {} brackets are obligatory, even when empty
        cell_square_bracket_options = list(self.tabularray_cell_square_bracket_options(table, cell_placement))
        cell_curly_bracket_options = list(self.tabularray_cell_curly_bracket_options(table, cell_placement))
        result[-1].content += Space(), LatexInline(
            r'\SetCell'
            + ('[' + ','.join(cell_square_bracket_options) + ']' if cell_square_bracket_options else '')
            + '{' + ','.join(cell_curly_bracket_options) + '}')

        if len(cell.content) > 0:
            # Open the bracket for the cell content
            result[-1].content += LatexInline('{'), Space()

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
                # which will be later processed by LatexBuilder to remove unnecessary newlines.
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
        yield f'rowhead={len(table.head.content)}'
        yield 'cells={valign=t}'

    def tabularray_cell_square_bracket_options(self, table: Table, cell_placement: CellPlacement) -> Sequence[str]:
        # pylint: disable=unused-argument
        cell = cell_placement.cell
        if cell.rowspan > 1:
            yield f'r={cell.rowspan}'
        if cell.colspan > 1:
            yield f'c={cell.colspan}'

    def tabularray_cell_curly_bracket_options(self, table: Table, cell_placement: CellPlacement) -> Sequence[str]:
        # pylint: disable=unused-argument
        return []
