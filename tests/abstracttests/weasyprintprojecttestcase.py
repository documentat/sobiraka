from abc import ABCMeta

from sobiraka.models import Status
from sobiraka.processing.weasyprint import WeasyPrintBuilder
from sobiraka.runtime import RT

from .abstractvisualpdftestcase import AbstractVisualPdfTestCase


class WeasyPrintProjectTestCase(AbstractVisualPdfTestCase[WeasyPrintBuilder], metaclass=ABCMeta):
    REQUIRE = Status.PROCESS4

    def _init_builder(self):
        return WeasyPrintBuilder(self.project.documents[0], RT.TMP / 'test.pdf')


del AbstractVisualPdfTestCase
