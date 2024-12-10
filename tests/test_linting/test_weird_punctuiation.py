from textwrap import dedent
from unittest import main

from abstracttests.abstractlintingtest import AbstractLintingTest


class TestWeirdPunctuation(AbstractLintingTest):
    SOURCE = '''
        Ellipsis... Ellipsis and spaces...    And one more ellipsis... Also, exclamation point! Or even two!! And how about a question mark? How about it?! I hope it all works.
        
        - This phrase does not end with a punctuation mark
        - This one doesn't either
    '''

    EXPECTED_PHRASES = (
        'Ellipsis...',
        'Ellipsis and spaces...',
        'And one more ellipsis...',
        'Also, exclamation point!',
        'Or even two!!',
        'And how about a question mark?',
        'How about it?!',
        'I hope it all works.',
        'This phrase does not end with a punctuation mark',
        "This one doesn't either",
    )


del AbstractLintingTest

if __name__ == '__main__':
    main()
