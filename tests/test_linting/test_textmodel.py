import re
from textwrap import dedent
from unittest import main, TestCase

from sobiraka.linter.textmodel import TextModel


class TestTextModel(TestCase):
    def setUp(self) -> None:
        self.tm = TextModel(
            lines=[
                'Hello World. I am a T.E.X.T.',
                'Do you know any other T.E.X.Ts?',
                'I would like to see them. I am lonely.',
                'Thank you.',
            ],
            fragments=[],
            exceptions_regexp=re.compile(r'\bT\.E\.X\.Ts?\b'))

    def test_text(self):
        expected = dedent('''
            Hello World. I am a T.E.X.T.
            Do you know any other T.E.X.Ts?
            I would like to see them. I am lonely.
            Thank you.
        ''').strip()
        actual = self.tm.text
        self.assertEqual(expected, actual)

    def test_exceptions_by_line(self):
        expected = (
            ('T.E.X.T',),
            ('T.E.X.Ts',),
            (),
            (),
        )
        actual = tuple(tuple(p.text for p in line) for line in self.tm.exceptions_by_line)
        self.assertEqual(expected, actual)

    def test_exceptions(self):
        expected = (
            'T.E.X.T',
            'T.E.X.Ts',
        )
        actual = tuple(p.text for p in self.tm.exceptions)
        self.assertEqual(expected, actual)

    def test_naive_phrases(self):
        expected = (
            ('Hello World.', 'I am a T.', 'E.', 'X.', 'T.',),
            ('Do you know any other T.', 'E.', 'X.', 'Ts?',),
            ('I would like to see them.', 'I am lonely.',),
            ('Thank you.',),
        )
        actual = tuple(tuple(p.text for p in line) for line in self.tm.naive_phrases)
        self.assertEqual(expected, actual)

    def test_phrases(self):
        expected = (
            'Hello World.',
            'I am a T.E.X.T.',
            'Do you know any other T.E.X.Ts?',
            'I would like to see them.',
            'I am lonely.',
            'Thank you.',
        )
        actual = tuple(p.text for p in self.tm.phrases)
        self.assertEqual(expected, actual)

    def test_clean_phrases(self):
        expected = (
            'Hello World.',
            'I am a        .',
            'Do you know any other         ?',
            'I would like to see them.',
            'I am lonely.',
            'Thank you.',
        )
        actual = tuple(self.tm.clean_phrases)
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    main()