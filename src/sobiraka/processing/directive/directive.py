import shlex
from abc import ABCMeta
from argparse import ArgumentError, ArgumentParser
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from panflute import Block, Cite, Doc, Element, Null, Para, Space, Str, stringify
from sobiraka.models import Issue, Page
from sobiraka.utils import all_subclasses

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
    DIRECTIVE_NAME: str

    @classmethod
    def set_up_arguments(cls, parser: ArgumentParser):
        pass

    @final
    def __init__(self, builder: 'Builder', page: Page, _: list[str] = None):
        self.builder: 'Builder' = builder
        self.page: Page = page

    def __repr__(self):
        return f'<{self.__class__.__name__} on {str(self.page.location)!r}>'

    def process(self):
        pass

    def postprocess(self) -> Block | None:
        return None


def para_to_directive(elem: Element, _: Doc, *, builder: 'Builder', page: Page) -> Element:
    try:
        # We only care about paragraphs that start with '@'
        assert isinstance(elem, Para)
        assert isinstance(elem.content[0], Cite)

        # Parse the line
        assert set(map(type, elem.content)) <= {Cite, Space, Str}
        directive_line = stringify(elem, newlines=False)
        directive_name, *arguments = shlex.split(directive_line)

    except AssertionError:
        return elem

    # Choose the Directive subclass based on the first word
    for directive_class in all_subclasses(Directive):
        if directive_class.DIRECTIVE_NAME == directive_name:
            break
    else:
        page.issues.append(UnknownDirective(directive_name))
        return Null()

    # Parse additional arguments into the Directive
    try:
        parser = ArgumentParser(allow_abbrev=False, add_help=False, exit_on_error=False)
        directive_class.set_up_arguments(parser)
        directive = directive_class(builder, page)

        # Ideally, we would just use parse_args(), and it would not exit the program thanks to exit_on_error.
        # However, as long as we try to support Python 3.11, we have to deal with a bug:
        # https://github.com/python/cpython/issues/103498
        _, unknown_args = parser.parse_known_args(arguments, namespace=directive)
        if unknown_args:
            raise ArgumentError(None, '')

        return directive

    except ArgumentError:
        page.issues.append(InvalidDirectiveArguments(directive_name))
        return Null()


@dataclass(order=True, frozen=True)
class UnknownDirective(Issue):
    directive: str

    def __str__(self):
        return f'Unknown directive {self.directive}'


@dataclass(order=True, frozen=True)
class InvalidDirectiveArguments(Issue):
    directive: str

    def __str__(self):
        return f'Invalid arguments for {self.directive}'
