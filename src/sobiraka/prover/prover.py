from asyncio import Task, create_task
from bisect import bisect_left, bisect_right
from typing import AsyncIterable

from more_itertools import unique_everseen
from panflute import Code, Element, ListItem, stringify
from typing_extensions import override

from sobiraka.models import Issue, MisspelledWords, Page, PageHref, PageStatus, PhraseBeginsWithLowerCase, Volume
from sobiraka.processing.abstract import VolumeBuilder
from sobiraka.processing.txt import Fragment, PlainTextDispatcher, TextModel, clean_phrases, exceptions_regexp
from sobiraka.runtime import RT
from .hunspell import run_hunspell
from ..utils import super_gather


class ProverProcessor(PlainTextDispatcher):
    def __init__(self, volume: Volume):
        super().__init__()
        self.volume: Volume = volume

    @override
    def _new_text_model(self) -> TextModel:
        return TextModel(exceptions_regexp=exceptions_regexp(self.volume))

    @override
    async def must_skip(self, elem: Element, page: Page) -> bool:
        return isinstance(elem, self.volume.config.prover.skip_elements)


class Prover(VolumeBuilder[ProverProcessor]):
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

        if self.volume.config.prover.dictionaries:
            words: list[str] = []
            for phrase in clean_phrases(phrases, tm.exceptions()):
                words += phrase.split()
            words = list(unique_everseen(words))
            misspelled_words: list[str] = []
            for word in await run_hunspell(words, self.volume):
                if word not in misspelled_words:
                    misspelled_words.append(word)
            if misspelled_words:
                RT[page].issues.append(MisspelledWords(page.path_in_project, tuple(misspelled_words)))

        for phrase in phrases:
            if self.volume.config.prover.checks.phrases_must_begin_with_capitals:
                async for issue in self.check__phrases_must_begin_with_capitals(phrase):
                    RT[page].issues.append(issue)

    @staticmethod
    async def check__phrases_must_begin_with_capitals(phrase: Fragment) -> AsyncIterable[Issue]:
        tm = phrase.tm

        if not phrase.text[0].islower():
            return

        for exception in tm.exceptions()[phrase.start.line]:
            if exception.start <= phrase.start < exception.end:
                return

        left = bisect_left(tm.fragments, phrase.start, key=lambda f: f.start)
        right = bisect_right(tm.fragments, phrase.start, key=lambda f: f.start)
        fragments_start_here = list(f for f in tm.fragments[left:right] if f.start == phrase.start)
        for fragment in fragments_start_here:
            match fragment.element:

                case Code():
                    return

                case ListItem() as li:
                    if stringify(li.parent.prev).rstrip().endswith(':'):
                        return

        yield PhraseBeginsWithLowerCase(phrase.text)
