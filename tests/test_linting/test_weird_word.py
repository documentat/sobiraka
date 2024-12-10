from textwrap import dedent
from unittest import main

from abstracttests.abstractlintingtest import AbstractLintingTest


class TestWeirdWord(AbstractLintingTest):
    EXCEPTIONS_REGEXPS = r'\bWe\.i\.RD\.wor\.d\.'

    SOURCE = '''
        - We.i.RD.wor.d. is at the beginning of a phrase.
        - Here We.i.RD.wor.d. is in the middle of a phrase.
        - This phrase ends with We.i.RD.wor.d.
        - Some phrase before. We.i.RD.wor.d. is at the beginning of a phrase. Some phrase after.
        - Some phrase before. Here We.i.RD.wor.d. is in the middle of a phrase. Some phrase after.
        - Some phrase before. This phrase ends with We.i.RD.wor.d. Some phrase after.
        - Multiple times We.i.RD.wor.d. We.i.RD.wor.d. We.i.RD.wor.d. in the middle of a phrase.
        - Multiple times We.i.RD.wor.d.We.i.RD.wor.d.We.i.RD.wor.d. in the middle of a phrase.
    '''

    EXPECTED_PHRASES = (
        'We.i.RD.wor.d. is at the beginning of a phrase.',
        'Here We.i.RD.wor.d. is in the middle of a phrase.',
        'This phrase ends with We.i.RD.wor.d.',
        'Some phrase before.',
        'We.i.RD.wor.d. is at the beginning of a phrase.',
        'Some phrase after.',
        'Some phrase before.',
        'Here We.i.RD.wor.d. is in the middle of a phrase.',
        'Some phrase after.',
        'Some phrase before.',
        'This phrase ends with We.i.RD.wor.d. Some phrase after.',
        'Multiple times We.i.RD.wor.d. We.i.RD.wor.d. We.i.RD.wor.d. in the middle of a phrase.',
        'Multiple times We.i.RD.wor.d.We.i.RD.wor.d.We.i.RD.wor.d. in the middle of a phrase.',
    )


del AbstractLintingTest

if __name__ == '__main__':
    main()
