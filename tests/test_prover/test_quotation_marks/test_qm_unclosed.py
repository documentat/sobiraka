import unittest
from unittest import TestCase

from sobiraka.prover.quotationsanalyzer import QuotationsAnalyzer
from sobiraka.utils import QuotationMark


class TestQM_Unclosed(TestCase):
    def test_qm_unclosed(self):
        lines = list(f'It is forbidden to {qm.opening}leave a quotation span unclosed.' for qm in QuotationMark)
        expected_issues = list(f'Unclosed quotation mark: {qm.opening}leave a quotation span unclosed.'
                               for qm in QuotationMark)

        analyzer = QuotationsAnalyzer(lines)
        actual_issues = list(map(str, analyzer.issues))
        self.assertSequenceEqual(expected_issues, actual_issues)


if __name__ == '__main__':
    unittest.main()
