import unittest
from unittest import TestCase

from sobiraka.prover.quotationsanalyzer import QuotationsAnalyzer
from sobiraka.utils import QuotationMark


class TestQM_Illegal(TestCase):
    def test_qm_illegal(self):
        lines = list(f'Can I use {qm.opening}these{qm.closing}?' for qm in QuotationMark)

        for allowed_qm in QuotationMark:
            with self.subTest(allowed_qm.name):
                analyzer = QuotationsAnalyzer(lines, [[allowed_qm]])

                expected_issues = list(f'Quotation marks {qm.value} are not allowed: {qm.opening}these{qm.closing}?'
                                       for qm in QuotationMark)
                actual_issues = list(map(str, analyzer.issues))
                self.assertSequenceEqual(expected_issues, actual_issues)


if __name__ == '__main__':
    unittest.main()
