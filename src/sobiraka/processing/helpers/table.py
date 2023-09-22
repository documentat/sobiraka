from abc import ABCMeta
from dataclasses import dataclass

from panflute import Table, TableBody, TableCell, TableHead, TableRow, stringify


@dataclass
class CellPlacement(metaclass=ABCMeta):
    """
    A wrapper for `cell` that knows both its “geometric” position in the grid (`i`, `j`)
    and its “counted” position (`counted_i`, `counted_j`).
    """
    cell: TableCell | None

    i: int = None
    j: int = None

    counted_i: int = None
    counted_j: int = None


class HeadCellPlacement(CellPlacement):
    def __repr__(self):
        return f'<HEAD[{self.i},{self.j}] {repr(stringify(self.cell)[:20])}>'


class BodyCellPlacement(CellPlacement):
    def __repr__(self):
        return f'<BODY[{self.i},{self.j}] {repr(stringify(self.cell)[:20])}>'


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
        text = repr(self.original)
        text = '<CONT ' + text[1:]
        return text

    @property
    def is_last_row(self) -> bool:
        return self.i == self.original.i + self.original.cell.rowspan - 1


def make_grid(table: Table) -> list[list[CellPlacement | CellContinuation]]:
    """
    Reads a table and returns a two-dimensional array, in which
    there is either a CellPlacement or a CellContinuation for each possible position.
    The first coordinate is the row number, the second coordinate is the column number.

    If you mentally split the result into two parts (head and body),
    then each element's `i` and `j` are set to the same values as its position in its part of the array.

    Below is the example of how `i` and `j` are assigned in a grid.
    Note that first lines of the head and the body have the same coordinates.
    To distinguish between them, you can check if an item is an instance of HeadCellPlacement or BodyCellPlacement.

        (0,0) (0,1) (0,2) ┐ HEAD
        (1,0) (1,1) (1,2) ┘
        (0,0) (0,1) (0,2) ┐ BODY
        (1,0) (1,1) (1,2) │
        (2,0) (2,1) (2,2) │
        (3,0) (3,1) (3,2) ┘

    The code assumes that `table.cols` (provided by panflute) is correct.
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    body: TableBody = table.content[0]
    head: TableHead = table.head
    all_rows: list[TableRow] = [*head.content, *body.content]

    headsize = len(head.content)
    rownum = len(all_rows)
    colnum = table.cols

    grid: list[list[CellPlacement | CellContinuation | None]] \
        = [[None for _ in range(colnum)] for _ in range(rownum)]

    # Iterate through table cells
    for i in range(rownum):
        iter_cells = iter(all_rows[i].content)
        for j in range(colnum):
            # Skip adding a new item if this place is already taken
            if grid[i][j] is not None:
                continue

            # Take the next cell and put it into current location in grid
            cell: TableCell = next(iter_cells)
            grid[i][j] = HeadCellPlacement(cell) if i < headsize else BodyCellPlacement(cell)

            # For a row-spanned cell, generate continuations for locations below current
            for continuation_i in range(i + 1, i + cell.rowspan):
                grid[continuation_i][j] = CellContinuation(grid[i][j])

            # For a col-spanned cell, generated continuations for locations right of current
            for continuation_j in range(j + 1, j + cell.colspan):
                grid[i][continuation_j] = CellContinuation(grid[i][j])

    # Set correct coordinates (i, j) for each grid item
    for i in range(headsize):
        for j in range(colnum):
            grid[i][j].i = i
            grid[i][j].j = j
    for i in range(headsize, rownum):
        for j in range(colnum):
            grid[i][j].i = i - headsize
            grid[i][j].j = j

    # Set correct “counted” coordinates (counted_i, counted_j) for each frid item
    for i in range(headsize, rownum):
        counted_j = 0
        for j in range(colnum):
            if isinstance(grid[i][j], CellPlacement):
                grid[i][j].counted_j = counted_j
                counted_j += 1
    for j in range(colnum):
        counted_i = 0
        for i in range(headsize, rownum):
            if isinstance(grid[i][j], CellPlacement):
                grid[i][j].counted_i = counted_i
                counted_i += 1

    return grid
