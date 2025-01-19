import unittest

from abstracttests.abstractprovertest import AbstractQuotationMarkTest
from sobiraka.utils import Apostrophe, QuotationMark

ALLOWED_QUOTATION_MARKS = (
    [QuotationMark.STRAIGHT_DOUBLE],
    [QuotationMark.CURVED_DOUBLE],
    [QuotationMark.ANGLED],
    [QuotationMark.ANGLED, QuotationMark.STRAIGHT_DOUBLE],
    [QuotationMark.ANGLED, QuotationMark.CURVED_DOUBLE],
)

ALLOWED_APOSTROPHES = Apostrophe.STRAIGHT,


class TestQM_Illegal_QuotationMarks(AbstractQuotationMarkTest):
    ALLOWED_QUOTATION_MARKS = ALLOWED_QUOTATION_MARKS
    ALLOWED_APOSTROPHES = ALLOWED_APOSTROPHES
    SOURCE = '''
        This config supports «angled», "straight double", and “curved double” quotation marks.
        It is forbidden to use ‘curved single’, ‚low single’, and „low double” quotation marks.
    '''
    EXPECTED_ISSUES = (
        'Curved single quotation marks are not allowed here: ‘curved single’',
        'Low single quotation marks are not allowed here: ‚low single’',
        'Low double quotation marks are not allowed here: „low double”',
    )


class TestQM_Illegal_Nestings(AbstractQuotationMarkTest):
    ALLOWED_QUOTATION_MARKS = ALLOWED_QUOTATION_MARKS
    ALLOWED_APOSTROPHES = ALLOWED_APOSTROPHES
    SOURCE = '''
        It is ok to use «"straight quotation marks" inside angled quotation marks».
        It is ok to use «“curved quotation marks” inside angled quotation marks».
        It is ok to use «both "straight quotation marks" and “curved quotation marks” inside angled quotation marks».
        It is forbidden to use "«angled quotation marks» inside straight quotation marks".
        It is forbidden to use “«angled quotation marks» inside curved quotation marks”.
    '''
    EXPECTED_ISSUES = (
        'Nesting order "«…»" is not allowed here: «angled quotation marks»',
        'Nesting order “«…»” is not allowed here: «angled quotation marks»',
    )


class TestQM_Illegal_Apostrophes(AbstractQuotationMarkTest):
    ALLOWED_QUOTATION_MARKS = ALLOWED_QUOTATION_MARKS
    ALLOWED_APOSTROPHES = ALLOWED_APOSTROPHES
    SOURCE = '''
        It's ok to use straight apostrophes.
        “It's ok” to use straight apostrophes.
        It’s forbidden to use curved apostrophes.
        “It’s forbidden” to use curved apostrophes.
    '''
    EXPECTED_ISSUES = (
        'Curved apostrophe is not allowed: It’s',
        'Curved apostrophe is not allowed: It’s',
    )


del AbstractQuotationMarkTest

if __name__ == '__main__':
    unittest.main()
