import unittest
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Sequence
from unittest import TestCase

from colorama import Fore

from sobiraka.utils import AbsolutePath, DictionaryValidator


class AbstractDictionaryValidatorTest(TestCase):
    AFF: str
    DIC: str

    AUTOFIX: bool = False

    EXPECTED_MESSAGES: Sequence[str] = ()

    @classmethod
    def setUpClass(cls):
        cls.dir = AbsolutePath(cls.enterClassContext(TemporaryDirectory(prefix='dictionary-')))

        cls.aff_path = cls.dir / 'dictionary.aff'
        cls.aff_path.write_text(dedent(cls.AFF).strip())

        cls.dic_path = cls.dir / 'dictionary.dic'
        cls.dic_path.write_text(dedent(cls.DIC).strip())

        cls.validator = DictionaryValidator(cls.aff_path, cls.dic_path)
        cls.validator.validate()

    def test_messages(self):
        self.assertEqual(self.EXPECTED_MESSAGES, self.validator.messages())


class AbstractDictionaryValidatorTest_Autofix(AbstractDictionaryValidatorTest):
    EXPECTED_FIXED_AFF: str = None
    EXPECTED_FIXED_DIC: str = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.validator.autofix()

    def test_autofix_aff(self):
        expected = dedent(self.EXPECTED_FIXED_AFF or self.AFF).strip()
        self.assertEqual(expected, self.aff_path.read_text())

    def test_autofix_dic(self):
        expected = dedent(self.EXPECTED_FIXED_DIC or self.DIC).strip()
        self.assertEqual(expected or self.DIC, self.dic_path.read_text())


class TestDictionaryValidator_NoIssues(AbstractDictionaryValidatorTest):
    AFF = '''
        SET UTF-8
        WORDCHARS 0123456789’-.
        BREAK 0
        NOSPLITSUGS
        MAXNGRAMSUGS 2
        ONLYMAXDIFF
        MAXDIFF 0
        
        SFX B N 10
        SFX B 0 а .
        SFX B 0 у .
        SFX B 0 ом .
        SFX B 0 е .
        SFX B 0 и [^бвгдзлмнпрстфц]
        SFX B 0 ы [бвгдзлмнпрстфц]
        SFX B 0 ов .
        SFX B 0 ам .
        SFX B 0 ами .
        SFX B 0 ах .
    '''

    DIC = '''
        3
        виджет/B
        инклюд/B
        инфоблок/B
    '''


class TestDictionaryValidator_UnknownAffix(AbstractDictionaryValidatorTest):
    AFF = '''
        SFX A N 1
        SFX A 0 a .
        
        SFX B N 1
        SFX B 0 b .
        
        SFX C N 1
        SFX C 0 c .
    '''

    DIC = '''
        4
        aaa/A
        bbb/B
        ccc/C
        ddd/D
    '''

    EXPECTED_MESSAGES = (
        Fore.RED + '[CRITICAL]  dictionary.dic:5 — Unknown affix: D',
    )


class TestDictionaryValidator_FixableAff(AbstractDictionaryValidatorTest_Autofix):
    AFF = '''
        SFX A N 100
        SFX A 0 a .
        SFX A 0 a .
        SFX A 0 a .
        
        SFX B N 2
        SFX B 0 b .
        SFX B 0 b .
        SFX B 0 b .
    '''

    DIC = '''
        2
        aaa/A
        bbb/B
    '''

    EXPECTED_FIXED_AFF = '''
        SFX A N 3
        SFX A 0 a .
        SFX A 0 a .
        SFX A 0 a .
        
        SFX B N 3
        SFX B 0 b .
        SFX B 0 b .
        SFX B 0 b .
    '''

    EXPECTED_MESSAGES = (
        Fore.GREEN + '[FIXED]     dictionary.aff:1 — Wrong affix size for A (should be 3)',
        Fore.GREEN + '[FIXED]     dictionary.aff:6 — Wrong affix size for B (should be 3)',
    )


class TestDictionaryValidator_FixableDic(AbstractDictionaryValidatorTest_Autofix):
    AFF = '''
    '''

    DIC = '''
        10
        aaa
        
        bbb
        
        ccc
        
    '''

    EXPECTED_FIXED_DIC = '''
        3
        aaa
        bbb
        ccc
    '''

    EXPECTED_MESSAGES = (
        Fore.GREEN + '[FIXED]     dictionary.dic:1 — Wrong dictionary size (should be 3)',
        Fore.GREEN + '[FIXED]     dictionary.dic:3 — Empty line in dictionary file',
        Fore.GREEN + '[FIXED]     dictionary.dic:5 — Empty line in dictionary file',
    )


class TestDictionaryValidator_InvalidLines(AbstractDictionaryValidatorTest):
    AFF = '''
        SFX A N 3
        SFX A 0 a .
        SFX A 0 a .
        SFX A 0 a .
        
        SFX B N 3
        SFX B 0 b .
        SFX B 0
        SFX B 0 b .
        
        SFX C N 3
        SFX C 0 c .
        SFX C 0 c .
        SFX C 0 c .
    '''

    DIC = '''
        3
        aaa/A
        aaa/B
        aaa/C
        aaa///
    '''

    EXPECTED_MESSAGES = (
        Fore.RED + '[CRITICAL]  dictionary.aff:8 — Invalid line, cannot parse further: SFX B 0',
        Fore.RED + '[CRITICAL]  dictionary.dic:4 — Unknown affix: C',
        Fore.RED + '[CRITICAL]  dictionary.dic:5 — Invalid line: aaa///',
    )


del AbstractDictionaryValidatorTest, AbstractDictionaryValidatorTest_Autofix

if __name__ == '__main__':
    unittest.main()
