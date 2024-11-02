from abc import ABCMeta

from sobiraka.models import PageStatus
from sobiraka.processing import WeasyPrintBuilder
from sobiraka.runtime import RT

from .abstractvisualpdftestcase import AbstractVisualPdfTestCase


class WeasyPrintProjectTestCase(AbstractVisualPdfTestCase[WeasyPrintBuilder], metaclass=ABCMeta):
    REQUIRE = PageStatus.PROCESS4

    def _init_builder(self):
        return WeasyPrintBuilder(self.project.volumes[0], RT.TMP / 'test.pdf')


del AbstractVisualPdfTestCase
