import unittest
from unittest import TestCase

from sobiraka.prover.quotationsanalyzer import QuotationsAnalyzer
from sobiraka.utils import QuotationMark

ALLOWED_QUOTATION_MARKS = list([x] for x in QuotationMark)


class TestQM_Unclosed(TestCase):
    def test_qm_unclosed(self):
        lines = list(f'It is forbidden to {qm.opening}leave a quotation span unclosed.' for qm in QuotationMark)

        # We should get a message about each line,
        # except for the one with a straight single mark
        # (it will be mistaken for an apostrophe)
        expected_issues = list(f'Unclosed quotation mark: {qm.opening}leave a quotation span unclosed.'
                               for qm in QuotationMark if qm is not QuotationMark.STRAIGHT_SINGLE)

        analyzer = QuotationsAnalyzer(lines, ALLOWED_QUOTATION_MARKS)
        actual_issues = list(map(str, analyzer.issues))
        self.assertEqual(expected_issues, actual_issues)


if __name__ == '__main__':
    unittest.main()
