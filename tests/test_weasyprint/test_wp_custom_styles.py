from unittest import main

from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from helpers.fakefilesystem import FakeFileSystem
from sobiraka.models import Page, Project, Volume
from sobiraka.models.config import Config, Config_PDF
from sobiraka.utils import RelativePath


class TestWeasyPrint_CustomStyles(WeasyPrintProjectTestCase):
    def _init_project(self) -> Project:
        fs = FakeFileSystem({
            RelativePath('theme/customstyle.css'): b'h1 { color: lightgreen; }'
        })

        config = Config(
            pdf=Config_PDF(
                custom_styles=(
                    RelativePath('theme/customstyle.css'),
                )))

        return Project(fs, {
            RelativePath(): Volume(config, {
                RelativePath(): Page('# Hello, world!\n The title above should be green.'),
            })
        })


del WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
