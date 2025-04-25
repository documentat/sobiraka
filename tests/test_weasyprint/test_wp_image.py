from unittest import main

from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project
from sobiraka.models.config import Config, Config_Paths
from sobiraka.utils import RelativePath


class TestWeasyPrint_Image(WeasyPrintProjectTestCase):
    def _init_project(self) -> Project:
        config = Config(
            paths=Config_Paths(
                root=RelativePath('src'),
                resources=RelativePath('images'),
            ),
            variables=dict(NOCOVER=True),
        )

        project = FakeProject({
            'src': FakeVolume(config, {
                'index.md': '# A circle\n![](/circle.svg)',
            })
        })

        project.fs.add_files({
            'images/circle.svg': '''
                <?xml version="1.0" encoding="UTF-8" standalone="no"?>
                <svg xmlns="http://www.w3.org/2000/svg" width="500" height="500">
                <circle cx="250" cy="250" r="210" fill="#fff" stroke="#000" stroke-width="8"/>
                </svg>
            ''',
        })

        return project


del WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
