import unittest
from unittest import TestCase

from sobiraka.prover.quotationsanalyzer import QuotationsAnalyzer
from sobiraka.utils import QuotationMark


class TestQM_Mismatching(TestCase):
    def test_qm_mismatching(self):
        for qm1 in QuotationMark:
            for qm2 in QuotationMark:
                if qm1.closing == qm2.closing:
                    continue
                with self.subTest(qm1=qm1.name, qm2=qm2.name):
                    analyzer = QuotationsAnalyzer([f'Here is a word: {qm1.opening}word{qm2.closing}.'])
                    expected_issues = [f'Mismatching quotation marks: {qm1.opening}word{qm2.closing}']
                    actual_issues = list(map(str, analyzer.issues))
                    self.assertSequenceEqual(expected_issues, actual_issues)


if __name__ == '__main__':
    unittest.main()
