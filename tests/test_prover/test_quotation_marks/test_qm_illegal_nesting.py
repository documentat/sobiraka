import unittest

from abstracttests.abstractprovertest import AbstractQuotationMarkTest
from sobiraka.utils import QuotationMark


class TestQM_IllegalNesting(AbstractQuotationMarkTest):
    ALLOWED_QUOTATION_MARKS = (
        [QuotationMark.STRAIGHT_DOUBLE],
        [QuotationMark.CURVED_DOUBLE],
        [QuotationMark.ANGLED],
        [QuotationMark.ANGLED, QuotationMark.STRAIGHT_DOUBLE],
        [QuotationMark.ANGLED, QuotationMark.CURVED_DOUBLE],
    )

    SOURCE = '''
        This config supports «angled», "straight double", and “curved double” quotation marks.
        It is ok to use «"straight quotation marks" inside angled quotation marks».
        It is ok to use «“curved quotation marks” inside angled quotation marks».
        It is ok to use «both "straight quotation marks" and “curved quotation marks” inside angled quotation marks».
        It is forbidden to use "«angled quotation marks» inside straight quotation marks".
        It is forbidden to use “«angled quotation marks» inside curved quotation marks”.
    '''

    EXPECTED_ISSUES = (
        'Nesting order "«»" is not allowed: «angled quotation marks» inside...',
        'Nesting order “«»” is not allowed: «angled quotation marks» inside...',
    )


del AbstractQuotationMarkTest

if __name__ == '__main__':
    unittest.main()
