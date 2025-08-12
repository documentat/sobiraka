import re
import shlex
from argparse import ArgumentError, ArgumentParser
from contextlib import suppress
from dataclasses import dataclass
from typing import Iterable, Sequence, TYPE_CHECKING

from panflute import Doc, Para, Space, Str, stringify

from sobiraka.models import Issue, Page
from sobiraka.runtime import RT
from sobiraka.utils import insert_after
from .directive import BlockDirective, BlockDirectiveClosing, Directive

if TYPE_CHECKING:
    from sobiraka.processing.abstract import Builder


def parse_directives(page: Page, builder: 'Builder'):
    _DirectiveParser(page, builder).parse()


class _DirectiveParser:
    def __init__(self, page: Page, builder: 'Builder'):
        self.page: Page = page
        self.builder: 'Builder' = builder
        self.unclosed_directive: BlockDirective | None = None

    def parse(self):
        RT[self.page].doc.walk(self.parse_para)

    def parse_para(self, para: Para, _: Doc):
        try:
            assert isinstance(para, Para)

            if para == Para(Str('@@')):
                self.unclosed_directive = None
                return BlockDirectiveClosing(self.builder, self.page)

            self.verify_syntax(para)

            directive_line = stringify(para, newlines=False)
            prefix, directive_name, arguments = self.split_components(directive_line)

            directive_class = self.choose_directive_class(prefix, directive_name)
            directive = self.instantiate_with_arguments(directive_class, arguments)

            if isinstance(directive, BlockDirective):
                self.unclosed_directive = directive
                if prefix == '@':
                    closing = BlockDirectiveClosing(self.builder, self.page)
                    insert_after(para.next, closing)

            return directive

        except (AssertionError, _DirectiveParserFailure):
            return None

    def verify_syntax(self, para: Para):
        assert isinstance(para, Para)
        assert set(map(type, para.content)) <= {Space, Str}
        assert isinstance(para.content[0], Str)
        assert para.content[0].text[0] == '@'

    def split_components(self, directive_line: str) -> tuple[str, str, Sequence[str]]:
        directive_name, *arguments = shlex.split(directive_line)
        prefix, directive_name = re.split(r'\b', directive_name, maxsplit=1)
        assert prefix in ('@', '@@')
        return prefix, directive_name, arguments

    @staticmethod
    def all_directive_classes(base: type[Directive] = Directive) -> Iterable[type[Directive]]:
        for subclass in base.__subclasses__():
            yield subclass
            yield from _DirectiveParser.all_directive_classes(subclass)

    def choose_directive_class(self, prefix: str, directive_name: str) -> type[Directive]:
        for directive_class in self.all_directive_classes():
            with suppress(AttributeError):
                if directive_class.DIRECTIVE_NAME == directive_name:
                    if prefix == '@@' and not issubclass(directive_class, BlockDirective):
                        self.page.issues.append(DirectiveIsNotABlock(directive_name))
                        raise _DirectiveParserFailure
                    return directive_class

        self.page.issues.append(UnknownDirective(directive_name))
        raise _DirectiveParserFailure

    def instantiate_with_arguments(self, directive_class: type[Directive], arguments: Sequence[str]) -> Directive:
        try:
            parser = ArgumentParser(allow_abbrev=False, add_help=False, exit_on_error=False)
            directive_class.set_up_arguments(parser)
            directive = directive_class(self.builder, self.page)

            # Ideally, we would just use parse_args(), and it would not exit the program thanks to exit_on_error.
            # However, as long as we try to support Python 3.11, we have to deal with a bug:
            # https://github.com/python/cpython/issues/103498
            _, unknown_args = parser.parse_known_args(arguments, namespace=directive)
            if unknown_args:
                raise ArgumentError(None, '')

            return directive

        except ArgumentError as exc:
            self.page.issues.append(InvalidDirectiveArguments(directive_class.DIRECTIVE_NAME))
            raise _DirectiveParserFailure from exc


class _DirectiveParserFailure(Exception):
    pass


# region Directive-related issues


@dataclass(order=True, frozen=True)
class UnknownDirective(Issue):
    directive: str

    def __str__(self):
        return f'Unknown directive @{self.directive}'


@dataclass(order=True, frozen=True)
class DirectiveIsNotABlock(Issue):
    directive: str

    def __str__(self):
        return f'You cannot use {self.directive} as a block directive'


@dataclass(order=True, frozen=True)
class UnexpectedClosing(Issue):
    def __str__(self):
        return 'You cannot use the closing directive @@ without using an opening first'


@dataclass(order=True, frozen=True)
class InvalidDirectiveArguments(Issue):
    directive: str

    def __str__(self):
        return f'Invalid arguments for @{self.directive}'

# endregion
