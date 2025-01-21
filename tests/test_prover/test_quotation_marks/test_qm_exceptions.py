import unittest

from abstracttests.abstractprovertest import AbstractQuotationMarkTest
from abstracttests.projecttestcase import NoExceptionsWereRaisesDuringTheTest


class TestQM_Exceptions(AbstractQuotationMarkTest):
    LANGUAGE = 'english'

    EXCEPTIONS_TXT = '''
        e“oi»re uu„pa
        G'prrg
    '''

    SOURCE = '''
        Hello. My name is e“oi»re uu„pa.
        I am from the G'prrg planet.
    '''

    EXPECTED_EXCEPTION_TYPES = {NoExceptionsWereRaisesDuringTheTest}


del AbstractQuotationMarkTest

if __name__ == '__main__':
    unittest.main()
