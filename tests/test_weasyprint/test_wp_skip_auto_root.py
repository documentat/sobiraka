from unittest import main

from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project


class TestWeasyPrint_SkipAutoRoot(WeasyPrintProjectTestCase):
    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                'page1.md': '# Page 1',
                'page2.md': '# Page 2',
            }),
        })


del WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
