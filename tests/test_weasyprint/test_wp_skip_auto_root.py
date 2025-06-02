from unittest import main

from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project
from sobiraka.models.config import Config, Config_Paths
from sobiraka.utils import RelativePath


class TestWeasyPrint_SkipAutoRoot(WeasyPrintProjectTestCase):
    def _init_project(self) -> Project:
        config = Config(
            paths=Config_Paths(root=RelativePath('src')),
            variables=dict(NOCOVER=True),
        )
        return FakeProject({
            'src': FakeVolume(config, {
                'page1.md': '# Page 1',
                'page2.md': '# Page 2',
            }),
        })


del WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
