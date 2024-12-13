from textwrap import dedent

from helpers import FakeFileSystem, assertNoDiff
from sobiraka.models import Page, PageStatus, Project, Syntax, Volume
from sobiraka.models.config import Config, Config_Prover, Config_Prover_Checks
from sobiraka.models.exceptions import IssuesOccurred
from sobiraka.processing.txt import TextModel
from sobiraka.prover import Prover
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath
from .projectdirtestcase import ProjectDirTestCase
from .projecttestcase import FailingProjectTestCase


class AbstractProverTest(ProjectDirTestCase[Prover]):
    maxDiff = None
    REQUIRE = PageStatus.PROCESS1

    CHECKS = Config_Prover_Checks()

    DICTIONARY_AFF: str = None
    DICTIONARY_DIC: str = ''

    EXCEPTIONS_TXT: str = ''
    EXCEPTIONS_REGEXPS: str = ''

    SYNTAX = Syntax.MD
    SOURCE: str

    EXPECTED_PHRASES: tuple[str]

    def _init_project(self) -> Project:
        fs = FakeFileSystem()
        config = Config(prover=Config_Prover(
            dictionaries=['en_US'],
            exceptions=[],
            checks=self.CHECKS,
        ))

        if self.DICTIONARY_DIC:
            config.prover.dictionaries.append('mydic')
            fs.pseudofiles[RelativePath('mydic.dic')] = dedent(self.DICTIONARY_DIC).strip()
            if self.DICTIONARY_AFF:
                fs.pseudofiles[RelativePath('mydic.aff')] = dedent(self.DICTIONARY_AFF).strip()
        if self.EXCEPTIONS_TXT:
            config.prover.exceptions.append(RelativePath('exceptions.txt'))
            fs.pseudofiles[RelativePath('exceptions.txt')] = dedent(self.EXCEPTIONS_TXT).strip()
        if self.EXCEPTIONS_REGEXPS:
            config.prover.exceptions.append(RelativePath('exceptions.regexp'))
            fs.pseudofiles[RelativePath('exceptions.regexp')] = dedent(self.EXCEPTIONS_REGEXPS).strip()

        page_filename = f'page.{self.SYNTAX.value}'
        self.page = Page(dedent(self.SOURCE).strip())

        return Project(fs, {
            RelativePath('src'): Volume(config, {
                RelativePath(page_filename): self.page,
            })
        })

    def _init_builder(self) -> Prover:
        return Prover(self.project.volumes[0])

    def tm(self, page: Page) -> TextModel:
        return self.builder.processor.tm[page]

    async def test_phrases(self):
        tm = self.tm(self.page)
        phrases = tuple(x.text for x in tm.phrases())
        assertNoDiff(self.EXPECTED_PHRASES, phrases)


class AbstractFailingProverTest(AbstractProverTest, FailingProjectTestCase):
    EXPECTED_EXCEPTION_TYPES = {IssuesOccurred}

    EXPECTED_ISSUES: tuple[str] = ()

    def test_issues(self):
        actual = tuple(map(str, RT[self.page].issues))
        self.assertEqual(self.EXPECTED_ISSUES, actual)


del ProjectDirTestCase
