from textwrap import dedent
from typing import Sequence

from helpers import assertNoDiff
from helpers.fakefilesystem import PseudoFiles
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Page, Project, Status, Syntax
from sobiraka.models.config import Config, Config_Paths, Config_Prover, Config_Prover_Dictionaries
from sobiraka.processing.abstract.waiter import IssuesOccurred
from sobiraka.processing.txt import TextModel
from sobiraka.prover import Prover
from sobiraka.utils import Apostrophe, QuotationMark, RelativePath
from .projecttestcase import FailingProjectTestCase, ProjectTestCase


class AbstractProverTest(ProjectTestCase[Prover]):
    maxDiff = None
    REQUIRE = Status.PROCESS

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

    EXPECTED_PHRASES: Sequence[str]

    def _init_project(self) -> Project:
        hunspell_dictionaries = []
        plaintext_dictionaries = []
        regexp_dictionaries = []
        pseudofiles: PseudoFiles = {}

        if self.LANGUAGE:
            hunspell_dictionaries.append('english')
        if self.DICTIONARY_DIC:
            hunspell_dictionaries.append(RelativePath('mydic.dic'))
            pseudofiles['mydic.dic'] = self.DICTIONARY_DIC
            if self.DICTIONARY_AFF:
                pseudofiles['mydic.aff'] = self.DICTIONARY_AFF
        if self.EXCEPTIONS_TXT:
            plaintext_dictionaries.append(RelativePath('exceptions.txt'))
            pseudofiles['exceptions.txt'] = self.EXCEPTIONS_TXT
        if self.EXCEPTIONS_REGEXPS:
            regexp_dictionaries.append(RelativePath('exceptions.regexp'))
            pseudofiles['exceptions.regexp'] = self.EXCEPTIONS_REGEXPS

        config = Config(
            paths=Config_Paths(
                root=RelativePath('volume'),
            ),
            prover=Config_Prover(
                dictionaries=Config_Prover_Dictionaries(
                    hunspell_dictionaries=tuple(hunspell_dictionaries),
                    plaintext_dictionaries=tuple(plaintext_dictionaries),
                    regexp_dictionaries=tuple(regexp_dictionaries),
                ),
                phrases_must_begin_with_capitals=self.PHRASES_MUST_BEGIN_WITH_CAPITALS,
                allowed_quotation_marks=tuple(map(tuple, self.ALLOWED_QUOTATION_MARKS)),
                allowed_apostrophes=tuple(self.ALLOWED_APOSTROPHES),
            )
        )

        page_filename = f'page.{self.SYNTAX.value}'

        project = FakeProject({
            'volume': FakeVolume(config, {
                page_filename: dedent(self.SOURCE).strip(),
            })
        })
        project.fs.add_files(pseudofiles)
        return project

    def _init_builder(self) -> Prover:
        return Prover(self.project.volumes[0])

    def tm(self, page: Page) -> TextModel:
        return self.builder.processor.tm[page]

    def test_phrases(self):
        _, page = self.project.get_volume().root.all_pages()

        tm = self.tm(page)
        phrases = tuple(x.text for x in tm.phrases())
        assertNoDiff(self.EXPECTED_PHRASES, phrases)


class AbstractFailingProverTest(AbstractProverTest, FailingProjectTestCase):
    EXPECTED_EXCEPTION_TYPES = {IssuesOccurred}

    EXPECTED_ISSUES: Sequence[str] = ()

    def test_issues(self):
        _, page = self.project.get_volume().root.all_pages()

        expected = '\n'.join(self.EXPECTED_ISSUES) + '\n'
        actual = '\n'.join(map(str, page.issues)) + '\n'
        self.assertEqual(expected, actual)


class AbstractQuotationMarkTest(AbstractFailingProverTest):
    LANGUAGE = None
    ALLOWED_QUOTATION_MARKS = (
        [QuotationMark.ANGLED],
        [QuotationMark.CURVED_DOUBLE],
        [QuotationMark.CURVED_SINGLE],
        [QuotationMark.GERMAN],
        [QuotationMark.STRAIGHT_DOUBLE],
        [QuotationMark.STRAIGHT_SINGLE],
    )
    test_phrases = None
