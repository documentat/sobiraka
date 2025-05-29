from unittest import main

from panflute import stringify

from abstracttests.abstracttestwithrt import AbstractTestWithRtTmp
from abstracttests.singlepageprojecttest import SinglePageProjectTest
from sobiraka.models import Status
from sobiraka.processing.latex import LatexBuilder
from sobiraka.processing.weasyprint import WeasyPrintBuilder
from sobiraka.processing.web import WebBuilder
from sobiraka.prover import Prover
from sobiraka.runtime import RT


class AbstractJinjaConditionsTestCase(SinglePageProjectTest, AbstractTestWithRtTmp):
    REQUIRE = Status.PARSE

    EXPECTED_VARIABLES: set[str]

    SOURCE = '''
        {%- if HTML -%}       HTML       {% endif -%}
        {%- if LATEX -%}      LATEX      {% endif -%}
        {%- if PDF -%}        PDF        {% endif -%}
        {%- if PROVER -%}     PROVER     {% endif -%}
        {%- if WEASYPRINT -%} WEASYPRINT {% endif -%}
        {%- if WEB -%}        WEB        {% endif -%}
    '''

    def test_page_source(self):
        actual = set(stringify(RT[self.page].doc).strip().split())
        self.assertSetEqual(self.EXPECTED_VARIABLES, actual)


class TestConditions_Latex(AbstractJinjaConditionsTestCase):
    EXPECTED_VARIABLES = {'LATEX', 'PDF'}

    def _init_builder(self):
        return LatexBuilder(self.project.get_volume(), RT.TMP / 'test.pdf')


class TestConditions_Prover(AbstractJinjaConditionsTestCase):
    EXPECTED_VARIABLES = {'HTML', 'LATEX', 'PDF', 'PROVER', 'WEASYPRINT', 'WEB'}

    def _init_builder(self):
        return Prover(self.project.get_volume())


class TestConditions_ProverWithVariables(AbstractJinjaConditionsTestCase):
    EXPECTED_VARIABLES = {'HTML', 'PDF'}

    def _init_builder(self):
        return Prover(self.project.get_volume(), dict(HTML=True, PDF=True))


class TestConditions_WeasyPrint(AbstractJinjaConditionsTestCase):
    EXPECTED_VARIABLES = {'HTML', 'PDF', 'WEASYPRINT'}

    def _init_builder(self):
        return WeasyPrintBuilder(self.project.get_volume(), RT.TMP / 'test.pdf')


class TestConditions_Web(AbstractJinjaConditionsTestCase):
    EXPECTED_VARIABLES = {'HTML', 'WEB'}

    def _init_builder(self):
        return WebBuilder(self.project, RT.TMP)


del AbstractJinjaConditionsTestCase, AbstractTestWithRtTmp, SinglePageProjectTest

if __name__ == '__main__':
    main()
