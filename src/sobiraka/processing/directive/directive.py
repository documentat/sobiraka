from abc import ABCMeta, abstractmethod

from panflute import Block

from sobiraka.models import Page
from ..abstract import Processor


class Directive(Block, metaclass=ABCMeta):
    """
    Base class for a directive in documentation sources.

    A directive is a command that starts with the `@` symbol, has a name and optionally some arguments.
    It must be placed in what Pandoc considers a separate paragraph
    (the most sure way to do it is to add newlines before and after).

    During an early step of processing, the code in `Processor` walks through all paragraphs in the document.
    If a paragraph begins with one of the known directive names, it replaces the paragraph with a `Directive`.
    Later, when the code in `Dispatcher` finds this element, it calls its `run()` function.

    Directives are convenient for implementing features that need to put generated Pandoc AST elements into pages.
    For example, `TocDirective` is used a placeholder that is later replaced with other AST elements,
    all without the need to render the generated content into a temporary Markdown or other syntax.
    """

    def __init__(self, processor: Processor, page: Page):
        self.processor: Processor = processor
        self.page: Page = page

    def __repr__(self):
        return f'<{self.__class__.__name__} on {str(self.page.path_in_project)!r}>'

    @abstractmethod
    async def run(self) -> tuple[Block, ...]:
        ...
