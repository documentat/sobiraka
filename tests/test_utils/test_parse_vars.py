from unittest import TestCase

from sobiraka.utils import parse_vars


class TestParseVars(TestCase):
    def test_all_boolean(self):
        actual = parse_vars(['KEY1', 'KEY2', 'KEY3'])
        expected = {'KEY1': True, 'KEY2': True, 'KEY3': True}
        self.assertEqual(expected, actual)

    def test_all_empty(self):
        actual = parse_vars(['KEY1=', 'KEY2=', 'KEY3='])
        expected = {'KEY1': '', 'KEY2': '', 'KEY3': ''}
        self.assertEqual(expected, actual)

    def test_all_normal(self):
        actual = parse_vars(['KEY1=VAL1', 'KEY2=VAL2', 'KEY3=VAL3'])
        expected = {'KEY1': 'VAL1', 'KEY2': 'VAL2', 'KEY3': 'VAL3'}
        self.assertEqual(expected, actual)

    def test_mixed(self):
        actual = parse_vars(['KEY1', 'KEY2=', 'KEY3=VAL3'])
        expected = {'KEY1': True, 'KEY2': '', 'KEY3': 'VAL3'}
        self.assertEqual(expected, actual)

    def test_none(self):
        actual = parse_vars([])
        expected = {}
        self.assertEqual(expected, actual)
