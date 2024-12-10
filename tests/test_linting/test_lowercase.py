from unittest import main

from abstracttests.abstractlintingtest import AbstractFailingLintingTest
from sobiraka.models import Syntax
from sobiraka.models.config import Config_Lint_Checks


class TestLowerCase(AbstractFailingLintingTest):
    CHECKS = Config_Lint_Checks(phrases_must_begin_with_capitals=True)

    EXCEPTIONS_TXT = '''
        PhraseBeginsWithLowerCase
        eXceptn
    '''

    SYNTAX = Syntax.RST
    SOURCE = '''
        Test for PhraseBeginsWithLowerCase
        ==================================
        
        a phrase must not begin with a lowercase letter. I repeat, a phrase must not begin with a lowercase letter.
        
        However, there are some exceptions from this rule.
        
        - ``x`` is an inline code snippet, and it may be in the beginning of a phrase.
        - eXceptn is an exception added to this book's dictionary, so it is always allowed.
        - that's it. No more exceptions. The phrase “that's it” earlier in this line is not allowed.
        - `even links <https://example.com/>`__ do not change anything.
        
        Any list item can begin with a lowercase letter if the whole list is preceded by a colon, for example:
        
        - this is allowed,
        - this is allowed,
        - this is allowed.
    '''

    EXPECTED_PHRASES = (
        'Test for PhraseBeginsWithLowerCase',
        'a phrase must not begin with a lowercase letter.',
        'I repeat, a phrase must not begin with a lowercase letter.',
        'However, there are some exceptions from this rule.',
        'x is an inline code snippet, and it may be in the beginning of a phrase.',
        "eXceptn is an exception added to this book's dictionary, so it is always allowed.",
        "that's it.",
        'No more exceptions.',
        "The phrase “that's it” earlier in this line is not allowed.",
        'even links do not change anything.',
        'Any list item can begin with a lowercase letter if the whole list is preceded by a colon, for example:',
        'this is allowed,',
        'this is allowed,',
        'this is allowed.',
    )

    EXPECTED_ISSUES = (
        'Phrase begins with a lowercase letter: a phrase must not begin with a...',
        "Phrase begins with a lowercase letter: that's it.",
        'Phrase begins with a lowercase letter: even links do not change anything.',
    )


del AbstractFailingLintingTest

if __name__ == '__main__':
    main()
