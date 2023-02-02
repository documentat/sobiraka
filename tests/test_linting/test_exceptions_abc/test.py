from unittest import main

from abstracttests.abstractlintingtest import AbstractLintingTest


class TestExceptionsAbc(AbstractLintingTest):
    pass


del AbstractLintingTest

if __name__ == '__main__':
    main()