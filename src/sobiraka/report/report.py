import sys
from contextlib import contextmanager

import rich
from rich import get_console
from rich.live import Live
from rich.text import Text
from rich.tree import Tree

from sobiraka.models import Document, Page, Source
from .widgets import SourceWidget, TreeAndBlankLine

_REPORTING = False
_LIVE: Live | None = None
_TREE = TreeAndBlankLine()
_SUBTREES: dict[Source | Page, Tree] = {}


@contextmanager
def run_beautifully():
    from sobiraka.processing.abstract.waiter import BuildFailure

    global _REPORTING  # pylint: disable=global-statement
    _REPORTING = True
    try:
        rich.reconfigure(markup=False, color_system='256')
        with Live(_TREE):
            try:
                yield
            finally:
                _TREE.extra_new_line = False
                Reporter.refresh()

    except BuildFailure:
        sys.exit(1)

    finally:
        _REPORTING = False


class Reporter:
    @staticmethod
    def register_document(document: Document):
        if not _REPORTING:
            return

        _SUBTREES[document.root] = _TREE.add(Text(str(document.root_path), style='yellow bold'), guide_style='grey66')

    @staticmethod
    def register_child_sources(source: Source):
        if not _REPORTING:
            return
        for child in source.child_sources:
            _SUBTREES[child] = _SUBTREES[source].add(SourceWidget(child))

    @staticmethod
    def register_pages(source: Source):
        if not _REPORTING:
            return

        if len(source.pages) == 1 and not source.child_sources:
            page = source.pages[0]
            _SUBTREES[source].label = SourceWidget(source, page)
            _SUBTREES[page] = _SUBTREES[source]

    @staticmethod
    def refresh():
        if not _REPORTING:
            return

        get_console()._live.refresh()  # pylint: disable=protected-access
