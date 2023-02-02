from unittest import main

from ..abstract_test_links_bad import AbstractTestLinksBad


class TestLinksBad_MD(AbstractTestLinksBad):
    EXT = 'md'


del AbstractTestLinksBad

if __name__ == '__main__':
    main()
