from unittest import TestCase

from sobiraka.models import Counter


class TestCounter(TestCase):
    def test_str(self):
        with self.subTest('1 component'):
            self.assertEqual('12', str(Counter([12])))

        with self.subTest('2 components'):
            self.assertEqual('12.34', str(Counter([12, 34])))

        with self.subTest('3 components'):
            self.assertEqual('12.34.56', str(Counter([12, 34, 56])))

    def test_repr(self):
        with self.subTest('1 component'):
            self.assertEqual('<Counter: 12>', repr(Counter([12])))

        with self.subTest('2 components'):
            self.assertEqual('<Counter: 12.34>', repr(Counter([12, 34])))

        with self.subTest('3 components'):
            self.assertEqual('<Counter: 12.34.56>', repr(Counter([12, 34, 56])))

    def test_increase_first_component(self):
        with self.subTest('1 component'):
            counter = Counter([12])
            counter.increase(1)
            self.assertEqual('13', str(counter))

        with self.subTest('2 components'):
            counter = Counter([12, 34])
            counter.increase(1)
            self.assertEqual('13', str(counter))

        with self.subTest('3 components'):
            counter = Counter([12, 34, 56])
            counter.increase(1)
            self.assertEqual('13', str(counter))

    def test_increase_last_component(self):
        with self.subTest('1 component'):
            counter = Counter([12])
            counter.increase(1)
            self.assertEqual('13', str(counter))

        with self.subTest('2 components'):
            counter = Counter([12, 34])
            counter.increase(2)
            self.assertEqual('12.35', str(counter))

        with self.subTest('3 components'):
            counter = Counter([12, 34, 56])
            counter.increase(3)
            self.assertEqual('12.34.57', str(counter))

    def test_increase_with_adding_new_component(self):
        with self.subTest('1 component'):
            counter = Counter([12])
            counter.increase(2)
            self.assertEqual('12.1', str(counter))

        with self.subTest('2 components'):
            counter = Counter([12, 34])
            counter.increase(3)
            self.assertEqual('12.34.1', str(counter))

        with self.subTest('3 components'):
            counter = Counter([12, 34, 56])
            counter.increase(4)
            self.assertEqual('12.34.56.1', str(counter))
