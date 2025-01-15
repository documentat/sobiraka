import unittest

from abstracttests.abstractprovertest import AbstractFailingProverTest
from abstracttests.projecttestcase import NoExceptionsWereRaisesDuringTheTest
from sobiraka.utils.quotationmark import QuotationMark


class AbstractQuotationMarkTest(AbstractFailingProverTest):
    LANGUAGE = None
    ALLOWED_QUOTATION_MARKS = [QuotationMark.STRAIGHT], [QuotationMark.CURLY], [QuotationMark.GUILLEMETS]
    test_phrases = None


class TestQuotationMarks(AbstractQuotationMarkTest):
    SOURCE = '''
        Sobiraka supports "straight quotation marks".
        Sobiraka supports “curly quotation marks”.
        Sobiraka supports «guillemets».
        Sobiraka supports "straight quotation marks", “curly quotation marks”, and «guillemets».
    '''

    EXPECTED_EXCEPTION_TYPES = {NoExceptionsWereRaisesDuringTheTest}
    EXPECTED_ISSUES = ()


class TestIllegalQuotationMarks_Straight(AbstractQuotationMarkTest):
    ALLOWED_QUOTATION_MARKS = [QuotationMark.CURLY], [QuotationMark.GUILLEMETS]

    SOURCE = '''
        It is forbidden to use "straight quotation marks".
        It is ok to use “curly quotation marks”.
        It is ok to use «guillemets».
    '''

    EXPECTED_ISSUES = (
        'Quotation marks "" are not allowed: "straight quotation marks".',
    )


class TestIllegalQuotationMarks_Curly(AbstractQuotationMarkTest):
    ALLOWED_QUOTATION_MARKS = [QuotationMark.STRAIGHT], [QuotationMark.GUILLEMETS]

    SOURCE = '''
        It is ok to use "straight quotation marks".
        It is forbidden to use “curly quotation marks”.
        It is ok to use «guillemets».
    '''

    EXPECTED_ISSUES = (
        'Quotation marks “” are not allowed: “curly quotation marks”.',
    )


class TestIllegalQuotationMarks_Guillemets(AbstractQuotationMarkTest):
    ALLOWED_QUOTATION_MARKS = [QuotationMark.STRAIGHT], [QuotationMark.CURLY]

    SOURCE = '''
        It is ok to use "straight quotation marks".
        It is ok to use “curly quotation marks”.
        It is forbidden to use «guillemets».
    '''

    EXPECTED_ISSUES = (
        'Quotation marks «» are not allowed: «guillemets».',
    )


class TestIllegalNesting(AbstractQuotationMarkTest):
    ALLOWED_QUOTATION_MARKS = (
        [QuotationMark.STRAIGHT],
        [QuotationMark.CURLY],
        [QuotationMark.GUILLEMETS],
        [QuotationMark.GUILLEMETS, QuotationMark.STRAIGHT],
        [QuotationMark.GUILLEMETS, QuotationMark.CURLY],
    )

    SOURCE = '''
        Sobiraka supports "straight quotation marks", “curly quotation marks”, and «guillemets».
        It is ok to use «"straight quotation marks" inside guillemets».
        It is ok to use «“curly quotation marks” inside guillemets».
        It is ok to use «both "straight quotation marks" and “curly quotation marks” inside guillemets».
        It is forbidden to use "«guillemets» inside straight quotation marks".
        It is forbidden to use “«guillemets» inside curly quotation marks”.
    '''

    EXPECTED_ISSUES = (
        'Nesting order "«»" is not allowed: «guillemets» inside straight...',
        'Nesting order “«»” is not allowed: «guillemets» inside curly...',
    )


class TestUnclosedSpans(AbstractQuotationMarkTest):
    ALLOWED_QUOTATION_MARKS = (
        [QuotationMark.STRAIGHT],
        [QuotationMark.CURLY],
        [QuotationMark.GUILLEMETS],
        [QuotationMark.GUILLEMETS, QuotationMark.STRAIGHT],
        [QuotationMark.GUILLEMETS, QuotationMark.CURLY],
    )

    SOURCE = '''
        It is forbidden to "leave a quotation span unclosed.
        It is forbidden to “leave a quotation span unclosed.
        It is forbidden to «leave a quotation span unclosed.
        It is forbidden to «leave a quotation span “unclosed.
        Closing quotation spans at the very end of the line «“is allowed.”»
    '''

    EXPECTED_ISSUES = (
        'Unclosed quotation mark: "leave a quotation span unclosed.',
        'Unclosed quotation mark: “leave a quotation span unclosed.',
        'Unclosed quotation mark: «leave a quotation span unclosed.',
        'Unclosed quotation mark: «leave a quotation span “unclosed.',
        'Unclosed quotation mark: “unclosed.',
    )


class MismatchingQuotationMarks_StraightOpening(AbstractQuotationMarkTest):
    SOURCE = '''
        You cannot use "mismatching“ quotation marks.
        You cannot use "mismatching” quotation marks.
        You cannot use "mismatching» quotation marks.
    '''

    EXPECTED_ISSUES = (
        'Mismatching quotation marks: "mismatching“',
        'Mismatching quotation marks: "mismatching”',
        'Mismatching quotation marks: "mismatching»',
    )


class MismatchingQuotationMarks_CurlyOpening(AbstractQuotationMarkTest):
    SOURCE = '''
        You cannot use “mismatching" quotation marks.
        You cannot use “mismatching“ quotation marks.
        You cannot use “mismatching» quotation marks.
    '''

    EXPECTED_ISSUES = (
        'Mismatching quotation marks: “mismatching"',
        'Mismatching quotation marks: “mismatching“',
        'Mismatching quotation marks: “mismatching»',
    )


class MismatchingQuotationMarks_GuillemetsOpening(AbstractQuotationMarkTest):
    SOURCE = '''
        You cannot use «mismatching" quotation marks.
        You cannot use «mismatching“ quotation marks.
        You cannot use «mismatching” quotation marks.
    '''

    EXPECTED_ISSUES = (
        'Mismatching quotation marks: «mismatching"',
        'Mismatching quotation marks: «mismatching“',
        'Mismatching quotation marks: «mismatching”',
    )


del AbstractFailingProverTest, AbstractQuotationMarkTest

if __name__ == '__main__':
    unittest.main()
