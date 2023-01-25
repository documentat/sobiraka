from functools import cached_property

from booktestcase import BookTestCase
from sobiraka.models import Page
from sobiraka.processing import SpellChecker


class TestSpellCheck(BookTestCase[SpellChecker]):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.page1, = self.book.pages

    @cached_property
    def processor(self) -> SpellChecker:
        return SpellChecker(self.book)

    def test_get_exceptions(self):
        self.assertSequenceEqual(self.processor.get_exceptions(), [r'B\.O\.O\.K\.'])

    async def test_get_phrases(self):
        expected_phrases: dict[Page, list[str]] = {
            self.page1: ['Hello wolrd!',
                         'Im writing a',
                         'I think it is veri good',
                         'Do you likee it?'],
        }
        for page, expected in expected_phrases.items():
            with self.subTest(page):
                actual = await self.processor.get_phrases(page)
                self.assertEqual(actual, expected)

    async def test_misspelled_words(self):
        expected_misspelled_words: dict[Page, list[str]] = {
            self.page1: ['wolrd', 'Im', 'veri', 'likee'],
        }
        await self.processor.run()
        for page, expected in expected_misspelled_words.items():
            with self.subTest(page):
                actual = self.processor.misspelled_words[page]
                self.assertEqual(actual, expected)


del BookTestCase