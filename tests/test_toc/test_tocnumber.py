from unittest import TestCase, main

from sobiraka.utils import TocNumber, Unnumbered


class TestTocNumber(TestCase):
    def test_str(self):
        data: tuple[tuple[str, TocNumber, str], ...] = (
            ('1 component', TocNumber(12), '12'),
            ('2 components', TocNumber(12, 34), '12.34'),
            ('3 components', TocNumber(12, 34, 56), '12.34.56'),
            ('Unnumbered', Unnumbered(), ''),
        )
        for name, number, expected in data:
            with self.subTest(name):
                actual = str(number)
                self.assertEqual(expected, actual)

    def test_format(self):
        data: tuple[tuple[str, TocNumber, str], ...] = (
            ('1 component', TocNumber(12), '<12>'),
            ('2 components', TocNumber(12, 34), '<12.34>'),
            ('3 components', TocNumber(12, 34, 56), '<12.34.56>'),
            ('Unnumbered', Unnumbered(), ''),
        )
        for name, number, expected in data:
            with self.subTest(name):
                actual = number.format('<{}>')
                self.assertEqual(expected, actual)

    def test_with_new_zero(self):
        data: tuple[tuple[str, TocNumber, str], ...] = (
            ('1 component', TocNumber(12), '12.0'),
            ('2 components', TocNumber(12, 34), '12.34.0'),
            ('3 components', TocNumber(12, 34, 56), '12.34.56.0'),
        )
        for name, number, expected in data:
            with self.subTest(name):
                actual = str(number.with_new_zero())
                self.assertEqual(expected, actual)

    def test_plus_1(self):
        data: tuple[tuple[str, TocNumber, str], ...] = (
            ('1 component', TocNumber(12), '13'),
            ('2 components', TocNumber(12, 34), '12.35'),
            ('3 components', TocNumber(12, 34, 56), '12.34.57'),
        )
        for name, number, expected in data:
            with self.subTest(name):
                actual = str(number + 1)
                self.assertEqual(expected, actual)

    def test_plus_2(self):
        data: tuple[tuple[str, TocNumber, str], ...] = (
            ('1 component', TocNumber(12), '14'),
            ('2 components', TocNumber(12, 34), '12.36'),
            ('3 components', TocNumber(12, 34, 56), '12.34.58'),
        )
        for name, number, expected in data:
            with self.subTest(name):
                actual = str(number + 2)
                self.assertEqual(expected, actual)

    def test_increased(self):
        data: tuple[tuple[TocNumber, int, str], ...] = (
            (TocNumber(12), 1, '13'),
            (TocNumber(12), 2, '12.1'),
            (TocNumber(12, 34), 1, '13'),
            (TocNumber(12, 34), 2, '12.35'),
            (TocNumber(12, 34), 3, '12.34.1'),
            (TocNumber(12, 34, 56), 1, '13'),
            (TocNumber(12, 34, 56), 2, '12.35'),
            (TocNumber(12, 34, 56), 3, '12.34.57'),
            (TocNumber(12, 34, 56), 4, '12.34.56.1'),
        )
        for number, level, expected in data:
            with self.subTest(f'{number} → {expected}'):
                actual = str(number.increased_at(level))
                self.assertEqual(expected, actual)


if __name__ == '__main__':
    main()
