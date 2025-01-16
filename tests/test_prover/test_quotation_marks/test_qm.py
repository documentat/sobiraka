import unittest
from unittest import TestCase

from more_itertools.more import all_unique

from sobiraka.utils import QuotationMark


class TestQuotationMark(TestCase):
    def test_unique_opening(self):
        self.assertTrue(all_unique(qm.opening for qm in QuotationMark),
                        msg='You have to carefully rethink the QuotationAnalyzer logic now.')


if __name__ == '__main__':
    unittest.main()
