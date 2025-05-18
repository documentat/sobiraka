import unittest
from abc import ABCMeta, abstractmethod
from textwrap import dedent

from typing_extensions import override

from abstracttests.abstracttestwithrt import AbstractTestWithRtTmp
from abstracttests.projecttestcase import ProjectTestCase
from sobiraka.models import Project, RealFileSystem, Status, Volume
from sobiraka.models.config import Config, Config_PDF, Config_Paths, Config_Theme, Config_Web
from sobiraka.processing.weasyprint import WeasyPrintBuilder
from sobiraka.processing.web import WebBuilder
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath


class TestSass(ProjectTestCase[WebBuilder], AbstractTestWithRtTmp, metaclass=ABCMeta):
    REQUIRE = Status.PROCESS4

    SPECIFY_FLAVOR = False
    SPECIFY_CUSTOM = False
    EXPECTED: str

    def _init_project(self) -> Project:
        return Project(RealFileSystem(AbsolutePath(__file__).parent), (
            Volume(None, None, Config(
                paths=Config_Paths(
                    root=RelativePath('src'),
                ),
                web=Config_Web(
                    theme=Config_Theme(
                        path=AbsolutePath(__file__).parent / 'my-theme',
                        flavor='icecream' if self.SPECIFY_FLAVOR else None,
                        customization=RelativePath() / 'my-theme' / 'custom.scss' if self.SPECIFY_CUSTOM else None,
                    ),
                ),
                pdf=Config_PDF(
                    theme=Config_Theme(
                        path=AbsolutePath(__file__).parent / 'my-theme',
                        flavor='icecream' if self.SPECIFY_FLAVOR else None,
                        customization=RelativePath() / 'my-theme' / 'custom.scss' if self.SPECIFY_CUSTOM else None,
                    ),
                ),
            )),
        ))

    @override
    async def _process(self):
        await self.builder.run()

    @abstractmethod
    def _actual_css(self) -> str: ...

    async def test_sass(self):
        expected = dedent(self.EXPECTED).strip()
        actual = self._actual_css().replace('}', '}\n').strip()
        self.assertEqual(expected, actual)


# region TestPrintSass

class TestPrintSass(TestSass, metaclass=ABCMeta):
    def _init_builder(self):
        return WeasyPrintBuilder(self.project.get_volume(), RT.TMP / 'test.pdf')

    @override
    def _actual_css(self) -> str:
        assert isinstance(self.builder, WeasyPrintBuilder)
        content_type, content = self.builder.pseudofiles['_static/theme.css']
        assert content_type == 'text/css'
        return content.decode()


class TestPrintSass_Default(TestPrintSass):
    EXPECTED = '''
        .print{foo:bar}
    '''


class TestPrintSass_WithCustom(TestPrintSass):
    SPECIFY_CUSTOM = True
    EXPECTED = '''
        .custom{foo:bar}
        .print{foo:bar}
    '''


class TestPrintSass_WithFlavor(TestPrintSass):
    SPECIFY_FLAVOR = True
    EXPECTED = '''
        .flavor{foo:bar}
        .print{foo:bar}
    '''


class TestPrintSass_WithFlavor_WithCustom(TestPrintSass):
    SPECIFY_FLAVOR = True
    SPECIFY_CUSTOM = True
    EXPECTED = '''
        .flavor{foo:bar}
        .custom{foo:bar}
        .print{foo:bar}
    '''


# endregion

# region TestWebSass

class TestWebSass(TestSass, metaclass=ABCMeta):
    def _init_builder(self):
        return WebBuilder(self.project, RT.TMP)

    @override
    def _actual_css(self) -> str:
        return (RT.TMP / '_static' / 'theme.css').read_text()


class TestWebSass_Default(TestWebSass):
    EXPECTED = '''
        .web{foo:bar}
    '''


class TestWebSass_WithCustom(TestWebSass):
    SPECIFY_CUSTOM = True
    EXPECTED = '''
        .custom{foo:bar}
        .web{foo:bar}
    '''


class TestWebSass_WithFlavor(TestWebSass):
    SPECIFY_FLAVOR = True
    EXPECTED = '''
        .flavor{foo:bar}
        .web{foo:bar}
    '''


class TestWebSass_WithFlavor_WithCustom(TestWebSass):
    SPECIFY_FLAVOR = True
    SPECIFY_CUSTOM = True
    EXPECTED = '''
        .flavor{foo:bar}
        .custom{foo:bar}
        .web{foo:bar}
    '''


# endregion


del TestSass, TestWebSass, TestPrintSass

if __name__ == '__main__':
    unittest.main()
