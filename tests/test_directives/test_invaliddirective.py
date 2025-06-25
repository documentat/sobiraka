import unittest

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from sobiraka.models import Status
from sobiraka.processing.abstract.waiter import IssuesOccurred


class TestInvalidDirective(SinglePageProjectTest):
    REQUIRE = Status.PROCESS3
    EXPECTED_EXCEPTION_TYPES = {IssuesOccurred}

    SOURCE = '''
        @haha --lol
        
        @toc --haha --lol
    '''

    EXPECTED_ISSUES = (
        'Unknown directive @haha',
        'Invalid arguments for @toc',
    )


del SinglePageProjectTest

if __name__ == '__main__':
    unittest.main()
