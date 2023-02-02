from unittest import main

from ..abstract_test_links_bad import AbstractTestLinksBad


class TestLinksBad_RST(AbstractTestLinksBad):
    EXT = 'rst'


del AbstractTestLinksBad

if __name__ == '__main__':
    main()
