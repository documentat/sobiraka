from unittest import main, skip

from abstracttests.abstractlintingtest import AbstractLintingTest


@skip('Linting is disabled temporarily.')
class TestWikipediaExampleCom(AbstractLintingTest):
    pass


del AbstractLintingTest

if __name__ == '__main__':
    main()
