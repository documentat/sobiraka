import unittest
from unittest import TestCase

from sobiraka.prover.quotationsanalyzer import QuotationsAnalyzer
from sobiraka.utils import QuotationMark

ALLOWED_QUOTATION_MARKS = list([x] for x in QuotationMark)


class TestQM_Mismatching(TestCase):
    def test_qm_mismatching(self):
        for qm1 in QuotationMark:
            for qm2 in QuotationMark:

                # Matching pairs are boring, don't test them
                if qm1.closing == qm2.closing:
                    continue

                # Apostrophe-like closings are stupid, that's not the case we're testing here
                if qm1 is QuotationMark.STRAIGHT_SINGLE:
                    continue
                if qm2 in (QuotationMark.CURVED_SINGLE, QuotationMark.STRAIGHT_SINGLE):
                    continue

                with self.subTest(qm1=qm1.name, qm2=qm2.name):
                    analyzer = QuotationsAnalyzer([f'Here is a word: {qm1.opening}word{qm2.closing}.'],
                                                  ALLOWED_QUOTATION_MARKS)
                    expected_issues = [f'Mismatching quotation marks: {qm1.opening}word{qm2.closing}']
                    actual_issues = list(map(str, analyzer.issues))
                    self.assertSequenceEqual(expected_issues, actual_issues)


if __name__ == '__main__':
    unittest.main()
