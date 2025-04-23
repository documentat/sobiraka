from argparse import ArgumentParser

from panflute import Block
from typing_extensions import override

from sobiraka.runtime import RT
from .directive import Directive


class ClassDirective(Directive):
    DIRECTIVE_NAME = '@class'

    id: str

    @classmethod
    @override
    def set_up_arguments(cls, parser: ArgumentParser):
        parser.add_argument('id')

    @override
    def process(self):
        block = self.next
        if not isinstance(block, Block):
            raise RuntimeError(f'Wait, where is the next block element? [{self.id}]')
        RT.CLASSES[id(block)] = self.id
