import re
from textwrap import dedent
from unittest import main
from unittest.mock import patch

import more_itertools
from panflute import stringify

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project
from sobiraka.processing.txt import PlainTextDispatcher, TextModel, clean_phrases
from sobiraka.runtime import RT


class AbstractTestTextModel(ProjectTestCase):
    SOURCE: str
    REGEXP: re.Pattern = None

    EXPECTED_TEXT: str = ''

    EXPECTED_EXCEPTIONS: tuple[tuple[str, ...], ...] = ()

    EXPECTED_NAIVE_PHRASES: tuple[tuple[str, ...], ...] = ()
    EXPECTED_PHRASES: tuple[str, ...] = ()
    EXPECTED_CLEAN_PHRASES: tuple[str, ...] = ()

    EXPECTED_SECTIONS: dict[str, str] = {}
    EXPECTED_SECTIONS_UP_TO_LEVEL: dict[int, dict[str, str]] = {}

    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                'index.md': dedent(self.SOURCE).strip(),
            }),
        })

    async def _process(self):
        await super()._process()
        page = self.project.get_volume().root_page

        with patch.object(PlainTextDispatcher, '_new_text_model',
                          return_value=TextModel(exceptions_regexp=self.REGEXP)):
            plain_text_dispatcher = PlainTextDispatcher()
            await plain_text_dispatcher.process_doc(RT[page].doc, page)
            self.tm = plain_text_dispatcher.tm[page]

    def test_text(self):
        expected = dedent(self.EXPECTED_TEXT).strip()
        actual = self.tm.text.rstrip('\n')
        self.assertEqual(expected, actual)

    def test_exceptions(self):
        actual = tuple(tuple(p.text for p in line) for line in self.tm.exceptions())
        actual = tuple(more_itertools.rstrip(actual, lambda x: x == ()))
        self.assertEqual(self.EXPECTED_EXCEPTIONS, actual)

    def test_naive_phrases(self):
        actual = tuple(tuple(p.text for p in line) for line in self.tm.naive_phrases())
        actual = tuple(more_itertools.rstrip(actual, lambda x: x == ()))
        self.assertEqual(self.EXPECTED_NAIVE_PHRASES, actual)

    def test_phrases(self):
        actual = tuple(p.text for p in self.tm.phrases())
        self.assertEqual(self.EXPECTED_PHRASES, actual)

    def test_clean_phrases(self):
        phrases = self.tm.phrases()
        exceptions = self.tm.exceptions()

        actual = tuple(clean_phrases(phrases, exceptions))
        self.assertEqual(self.EXPECTED_CLEAN_PHRASES, actual)

    def test_sections(self):
        expected = self.EXPECTED_SECTIONS or {'': dedent(self.EXPECTED_TEXT).strip()}
        actual = dict((anchor and stringify(anchor.header) or '', fragment.text.rstrip())
                      for anchor, fragment in self.tm.sections.items())
        self.assertEqual(expected, actual)

    def test_sections_up_to_level(self):
        for max_level, expected in self.EXPECTED_SECTIONS_UP_TO_LEVEL.items():
            with self.subTest(max_level=max_level):
                expected = {k: dedent(v).strip() for k, v in expected.items()}
                actual = dict((anchor and stringify(anchor.header) or '', fragment.text.rstrip())
                              for anchor, fragment in self.tm.sections_up_to_level(max_level).items())
                self.assertEqual(expected, actual)


class TestTextModel_Empty(AbstractTestTextModel):
    SOURCE = ''


class TestTextModel_EmptyButWithTitle(AbstractTestTextModel):
    SOURCE = '''
        # Empty page
    '''
    EXPECTED_TEXT = 'Empty page'
    EXPECTED_NAIVE_PHRASES = ('Empty page',),
    EXPECTED_PHRASES = 'Empty page',
    EXPECTED_CLEAN_PHRASES = 'Empty page',


class TestTextModel_WithException(AbstractTestTextModel):
    SOURCE = '''
        Hello World. I am a T.E.X.T.
        Do you know any other T.E.X.Ts?
    '''
    REGEXP = re.compile(r'\bT\.E\.X\.Ts?\b')

    EXPECTED_TEXT = '''
        Hello World. I am a T.E.X.T.
        Do you know any other T.E.X.Ts?
    '''
    EXPECTED_EXCEPTIONS = (
        ('T.E.X.T',),
        ('T.E.X.Ts',),
    )
    EXPECTED_NAIVE_PHRASES = (
        ('Hello World.', 'I am a T.', 'E.', 'X.', 'T.',),
        ('Do you know any other T.', 'E.', 'X.', 'Ts?',),
    )
    EXPECTED_PHRASES = (
        'Hello World.',
        'I am a T.E.X.T.',
        'Do you know any other T.E.X.Ts?',
    )
    EXPECTED_CLEAN_PHRASES = (
        'Hello World.',
        'I am a        .',
        'Do you know any other         ?',
    )


class TestTextModel_WithSections(AbstractTestTextModel):
    SOURCE = '''
        Top-level introduction.
        
        ## Section A
        Introduction.
        
        ### Section A1
        Text A1.
        
        ## Section B
        ### Section B1
        Text B1.
    '''

    EXPECTED_TEXT = '''
        Top-level introduction.
        Section A
        Introduction.
        Section A1
        Text A1.
        Section B
        Section B1
        Text B1.
    '''
    EXPECTED_NAIVE_PHRASES = (
        ('Top-level introduction.',),
        ('Section A',),
        ('Introduction.',),
        ('Section A1',),
        ('Text A1.',),
        ('Section B',),
        ('Section B1',),
        ('Text B1.',),
    )
    EXPECTED_PHRASES = (
        'Top-level introduction.',
        'Section A',
        'Introduction.',
        'Section A1',
        'Text A1.',
        'Section B',
        'Section B1',
        'Text B1.',
    )
    EXPECTED_CLEAN_PHRASES = (
        'Top-level introduction.',
        'Section A',
        'Introduction.',
        'Section A1',
        'Text A1.',
        'Section B',
        'Section B1',
        'Text B1.',
    )
    EXPECTED_SECTIONS = {
        '': 'Top-level introduction.',
        'Section A': 'Introduction.',
        'Section A1': 'Text A1.',
        'Section B': '',
        'Section B1': 'Text B1.',
    }
    EXPECTED_SECTIONS_UP_TO_LEVEL = {
        1: {
            '': '''
                Top-level introduction.
                Section A
                Introduction.
                Section A1
                Text A1.
                Section B
                Section B1
                Text B1.
            ''',
        },
        2: {
            '': 'Top-level introduction.',
            'Section A': '''
                Introduction.
                Section A1
                Text A1.
            ''',
            'Section B': '''
                Section B1
                Text B1.
            ''',
        },
        3: {
            '': 'Top-level introduction.',
            'Section A': 'Introduction.',
            'Section A1': 'Text A1.',
            'Section B': '',
            'Section B1': 'Text B1.',
        },
        4: {
            '': 'Top-level introduction.',
            'Section A': 'Introduction.',
            'Section A1': 'Text A1.',
            'Section B': '',
            'Section B1': 'Text B1.',
        },
        5: {
            '': 'Top-level introduction.',
            'Section A': 'Introduction.',
            'Section A1': 'Text A1.',
            'Section B': '',
            'Section B1': 'Text B1.',
        },
        6: {
            '': 'Top-level introduction.',
            'Section A': 'Introduction.',
            'Section A1': 'Text A1.',
            'Section B': '',
            'Section B1': 'Text B1.',
        },
    }


del AbstractTestTextModel

if __name__ == '__main__':
    main()
