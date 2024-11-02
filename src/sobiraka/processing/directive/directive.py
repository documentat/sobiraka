from abc import ABCMeta
from typing import TYPE_CHECKING

from panflute import Block

from sobiraka.models import Page

if TYPE_CHECKING:
    from ..abstract import Builder


class Directive(Block, metaclass=ABCMeta):
    """
    Base class for a directive in documentation sources.

    A directive is a command that starts with the `@` symbol, has a name and optionally some arguments.
    It must be placed in what Pandoc considers a separate paragraph
    (the most sure way to do it is to add newlines before and after).

    During an early step of building, the code in `Processor` walks through all paragraphs in the document.
    If a paragraph begins with one of the known directive names, it replaces the paragraph with a `Directive`.

    When the code in `Dispatcher` finds this element, it calls its `process()` function.
    At a later stage of building, the builder calls each directive's `postprocess()`.

    Directives are convenient for implementing features that need to put generated Pandoc AST elements into pages.
    For example, `TocDirective` is used a placeholder that is later replaced with other AST elements,
    all without the need to render the generated content into a temporary Markdown or other syntax.
    """

    def __init__(self, builder: 'Builder', page: Page):
        self.builder: 'Builder' = builder
        self.page: Page = page

    def __repr__(self):
        return f'<{self.__class__.__name__} on {str(self.page.path_in_project)!r}>'

    def process(self):
        pass

    def postprocess(self):
        pass
