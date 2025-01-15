import re
from asyncio import Task, create_task
from functools import cached_property

from more_itertools import unique_everseen
from panflute import Element
from typing_extensions import override

from sobiraka.models import Page, PageHref, PageStatus, Volume
from sobiraka.models.issues import MisspelledWords
from sobiraka.processing.abstract import VolumeBuilder
from sobiraka.processing.txt import PlainTextDispatcher, TextModel, clean_phrases
from sobiraka.runtime import RT
from sobiraka.utils import super_gather
from .checks import phrases_must_begin_with_capitals
from .hunspell import run_hunspell
from .quotationsanalyzer import QuotationsAnalyzer


class ProverProcessor(PlainTextDispatcher):
    def __init__(self, volume: Volume):
        super().__init__()
        self.volume: Volume = volume

    @override
    def _new_text_model(self) -> TextModel:
        return TextModel(exceptions_regexp=self.exceptions_regexp)

    @override
    async def must_skip(self, elem: Element, page: Page) -> bool:
        return isinstance(elem, self.volume.config.prover.skip_elements)

    @cached_property
    def exceptions_regexp(self) -> re.Pattern | None:
        """
        Prepare a regular expression that matches any exception.
        If the volume declares no exceptions, returns `None`.
        """
        dictionaries = self.volume.config.prover.dictionaries
        fs = self.volume.project.fs

        regexp_parts: list[str] = []

        for dictionary in dictionaries.plaintext_dictionaries:
            lines = fs.read_text(dictionary).splitlines()
            for line in lines:
                regexp_parts.append(r'\b' + re.escape(line.strip()) + r'\b')

        for dictionary in dictionaries.regexp_dictionaries:
            lines = fs.read_text(dictionary).splitlines()
            for line in lines:
                regexp_parts.append(line.strip())

        if regexp_parts:
            return re.compile('|'.join(regexp_parts))
        return None


class Prover(VolumeBuilder[ProverProcessor]):
    def __init__(self, volume: Volume, variables: dict = None):
        super().__init__(volume)
        self._variables: dict = variables or {}

    @override
    def additional_variables(self) -> dict:
        return self._variables or dict(
            HTML=True,
            LATEX=True,
            PDF=True,
            PROVER=True,
            WEASYPRINT=True,
            WEB=True,
        )

    @override
    def init_processor(self) -> ProverProcessor:
        return ProverProcessor(self.volume)

    @override
    def make_internal_url(self, href: PageHref, *, page: Page = None) -> str:
        raise NotImplementedError

    @override
    async def run(self):
        tasks: list[Task] = []
        for page in self.volume.pages:
            tasks.append(create_task(self.require(page, PageStatus.PROCESS1), name=f'checking {page.path_in_project}'))
        await super_gather(tasks)

    @override
    async def process1(self, page: Page):
        await super().process1(page)
        tm = self.processor.tm[page]

        phrases = tm.phrases()

        fs = self.volume.project.fs
        config = self.volume.config.prover

        if config.dictionaries.hunspell_dictionaries:
            words: list[str] = []
            for phrase in clean_phrases(phrases, tm.exceptions()):
                words += phrase.split()
            words = list(unique_everseen(words))
            misspelled_words: list[str] = []
            for word in await run_hunspell(words, fs, config.dictionaries.hunspell_dictionaries):
                if word not in misspelled_words:
                    misspelled_words.append(word)
            if misspelled_words:
                RT[page].issues.append(MisspelledWords(page.path_in_project, tuple(misspelled_words)))

        if config.phrases_must_begin_with_capitals:
            RT[page].issues += phrases_must_begin_with_capitals(tm, phrases)

        if config.allowed_quotation_marks:
            quotation_analyzer = QuotationsAnalyzer(tm, config.allowed_quotation_marks)
            RT[page].issues += quotation_analyzer.issues
