from textwrap import dedent
from typing import Sequence

from helpers import FakeFileSystem, assertNoDiff
from sobiraka.models import Page, PageStatus, Project, Syntax, Volume
from sobiraka.models.config import Config, Config_Prover, Config_Prover_Dictionaries
from sobiraka.models.exceptions import IssuesOccurred
from sobiraka.processing.txt import TextModel
from sobiraka.prover import Prover
from sobiraka.runtime import RT
from sobiraka.utils import Apostrophe, QuotationMark, RelativePath
from .projectdirtestcase import ProjectDirTestCase
from .projecttestcase import FailingProjectTestCase


class AbstractProverTest(ProjectDirTestCase[Prover]):
    maxDiff = None
    REQUIRE = PageStatus.PROCESS1

    PHRASES_MUST_BEGIN_WITH_CAPITALS = False
    ALLOWED_QUOTATION_MARKS: Sequence[Sequence[QuotationMark]] = ()
    ALLOWED_APOSTROPHES: Sequence[Apostrophe] = ()

    LANGUAGE: str | None = 'english'
    DICTIONARY_AFF: str = None
    DICTIONARY_DIC: str = ''

    EXCEPTIONS_TXT: str = ''
    EXCEPTIONS_REGEXPS: str = ''

    SYNTAX = Syntax.MD
    SOURCE: str

    EXPECTED_PHRASES: tuple[str]

    def _init_project(self) -> Project:
        fs = FakeFileSystem()
        hunspell_dictionaries = []
        plaintext_dictionaries = []
        regexp_dictionaries = []

        if self.LANGUAGE:
            hunspell_dictionaries.append('english')
        if self.DICTIONARY_DIC:
            hunspell_dictionaries.append(RelativePath('mydic.dic'))
            fs.pseudofiles[RelativePath('mydic.dic')] = dedent(self.DICTIONARY_DIC).strip()
            if self.DICTIONARY_AFF:
                fs.pseudofiles[RelativePath('mydic.aff')] = dedent(self.DICTIONARY_AFF).strip()
        if self.EXCEPTIONS_TXT:
            plaintext_dictionaries.append(RelativePath('exceptions.txt'))
            fs.pseudofiles[RelativePath('exceptions.txt')] = dedent(self.EXCEPTIONS_TXT).strip()
        if self.EXCEPTIONS_REGEXPS:
            regexp_dictionaries.append(RelativePath('exceptions.regexp'))
            fs.pseudofiles[RelativePath('exceptions.regexp')] = dedent(self.EXCEPTIONS_REGEXPS).strip()

        config = Config(prover=Config_Prover(
            dictionaries=Config_Prover_Dictionaries(
                hunspell_dictionaries=tuple(hunspell_dictionaries),
                plaintext_dictionaries=tuple(plaintext_dictionaries),
                regexp_dictionaries=tuple(regexp_dictionaries),
            ),
            phrases_must_begin_with_capitals=self.PHRASES_MUST_BEGIN_WITH_CAPITALS,
            allowed_quotation_marks=tuple(map(tuple, self.ALLOWED_QUOTATION_MARKS)),
            allowed_apostrophes=tuple(self.ALLOWED_APOSTROPHES),
        ))

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

    def test_phrases(self):
        tm = self.tm(self.page)
        phrases = tuple(x.text for x in tm.phrases())
        assertNoDiff(self.EXPECTED_PHRASES, phrases)


class AbstractFailingProverTest(AbstractProverTest, FailingProjectTestCase):
    EXPECTED_EXCEPTION_TYPES = {IssuesOccurred}

    EXPECTED_ISSUES: tuple[str] = ()

    def test_issues(self):
        expected = '\n'.join(self.EXPECTED_ISSUES) + '\n'
        actual = '\n'.join(map(str, RT[self.page].issues)) + '\n'
        self.assertEqual(expected, actual)


class AbstractQuotationMarkTest(AbstractFailingProverTest):
    LANGUAGE = None
    ALLOWED_QUOTATION_MARKS = (
        [QuotationMark.ANGLED],
        [QuotationMark.CURVED_DOUBLE],
        [QuotationMark.CURVED_SINGLE],
        [QuotationMark.LOW_DOUBLE],
        [QuotationMark.LOW_SINGLE],
        [QuotationMark.STRAIGHT_DOUBLE],
        [QuotationMark.STRAIGHT_SINGLE],
    )
    test_phrases = None


del ProjectDirTestCase
