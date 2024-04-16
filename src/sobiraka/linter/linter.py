from asyncio import gather
from bisect import bisect_left, bisect_right
from typing import AsyncIterable, Awaitable

from more_itertools import unique_everseen
from panflute import Code, ListItem, stringify

from sobiraka.models import Issue, MisspelledWords, Page, PhraseBeginsWithLowerCase
from sobiraka.processing.abstract import VolumeProcessor
from sobiraka.processing.txt import Fragment, PlainTextDispatcher, TextModel, exceptions_regexp
from sobiraka.runtime import RT
from .hunspell import run_hunspell


# TODO: Reorganize Processor and related abstract classes
# pylint: disable=abstract-method
class Linter(PlainTextDispatcher, VolumeProcessor):

    def _new_text_model(self) -> TextModel:
        return TextModel(exceptions_regexp=exceptions_regexp(self.volume))

    async def run(self):
        tasks: list[Awaitable] = []
        for page in self.volume.pages:
            tasks.append(self.check_page(page))
        await gather(*tasks)

        for page in self.get_pages():
            if RT[page].issues:
                return 1
        return 0

    async def check_page(self, page: Page):
        tm = self.tm[page]

        if self.volume.config.lint.dictionaries:
            words: list[str] = []
            for phrase in tm.clean_phrases:
                words += phrase.split()
            words = list(unique_everseen(words))
            misspelled_words: list[str] = []
            async for word in run_hunspell(words, self.volume):
                if word not in misspelled_words:
                    misspelled_words.append(word)
            if misspelled_words:
                RT[page].issues.append(MisspelledWords(page.path_in_project, tuple(misspelled_words)))

        for phrase in tm.phrases:
            if self.volume.config.lint.checks.phrases_must_begin_with_capitals:
                async for issue in self.check__phrases_must_begin_with_capitals(phrase):
                    RT[page].issues.append(issue)

    @staticmethod
    async def check__phrases_must_begin_with_capitals(phrase: Fragment) -> AsyncIterable[Issue]:
        tm = phrase.tm

        if not phrase.text[0].islower():
            return

        for exception in tm.exceptions[phrase.start.line]:
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
