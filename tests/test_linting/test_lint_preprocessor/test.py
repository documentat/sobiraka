from unittest import main

from panflute import Space, Str

from abstracttests.abstractlintingtest import AbstractLintingTest
from testutils import assertNoDiff


class TestLintPreprocessor(AbstractLintingTest):

    async def test_lines(self):
        for page, expected in self.for_each_expected('.lines'):
            with self.subTest(page):
                expected = expected.read_text().splitlines()
                while expected[-1] == '':
                    expected.pop()

                tm = await self.processor.tm(page)
                actual = tm.lines
                while actual[-1] == '':
                    actual.pop()

                assertNoDiff(expected, actual)

    async def test_fragments(self):
        for page, expected in self.for_each_expected('.fragments'):
            with self.subTest(page):
                expected = list(filter(None, (f.strip() for f in expected.read_text().splitlines())))

                actual: list[str] = []
                tm = await self.processor.tm(page)
                self.assertSequenceEqual(sorted(tm.fragments, key=lambda f: f.start), tm.fragments)

                for f in tm.fragments:
                    if not isinstance(f.element, (Str, Space)):
                        text = f.text.strip().replace('\n', r' \n ')
                        actual.append(f'[{f.start}-{f.end}][{f.element.tag}] {text}'.rstrip())

                assertNoDiff(expected, actual)


del AbstractLintingTest

if __name__ == '__main__':
    main()