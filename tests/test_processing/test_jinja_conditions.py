from textwrap import dedent
from unittest import main
from unittest.mock import Mock

from panflute import stringify

from abstracttests.abstracttestwithrt import AbstractTestWithRtTmp
from abstracttests.projecttestcase import ProjectTestCase
from sobiraka.models import FileSystem, Page, PageStatus, Project, Volume
from sobiraka.processing.latex import LatexBuilder
from sobiraka.processing.weasyprint import WeasyPrintBuilder
from sobiraka.processing.web import WebBuilder
from sobiraka.prover import Prover
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath


class AbstractJinjaConditionsTestCase(ProjectTestCase, AbstractTestWithRtTmp):
    REQUIRE = PageStatus.PREPARE

    EXPECTED_VARIABLES: set[str]

    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            RelativePath('src'): Volume({
                RelativePath('page.md'): Page(dedent('''
                    {%- if HTML -%}       HTML       {% endif -%}
                    {%- if LATEX -%}      LATEX      {% endif -%}
                    {%- if PDF -%}        PDF        {% endif -%}
                    {%- if PROVER -%}     PROVER     {% endif -%}
                    {%- if WEASYPRINT -%} WEASYPRINT {% endif -%}
                    {%- if WEB -%}        WEB        {% endif -%}
                ''')),
            })
        })

    def test_page_source(self):
        page = self.project.pages[-1]
        actual = set(stringify(RT[page].doc).strip().split())
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


del AbstractJinjaConditionsTestCase, AbstractTestWithRtTmp

if __name__ == '__main__':
    main()
