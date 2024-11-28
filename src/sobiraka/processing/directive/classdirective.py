from typing import TYPE_CHECKING

from panflute import Block

from sobiraka.models import Page
from sobiraka.runtime import RT
from .directive import Directive

if TYPE_CHECKING:
    from ..abstract import Builder


class ClassDirective(Directive):
    def __init__(self, builder: 'Builder', page: Page, argv: list[str]):
        super().__init__(builder, page)

        assert len(argv) == 1
        self.id: str = argv[0]

    def process(self):
        block = self.next
        if not isinstance(block, Block):
            raise RuntimeError(f'Wait, where is the next block element? [{self.id}]')
        RT.CLASSES[id(block)] = self.id
