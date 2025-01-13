from textwrap import dedent
from unittest import main

from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from helpers import FakeFileSystem
from sobiraka.models import Page, Project, Volume
from sobiraka.models.config import Config, Config_PDF
from sobiraka.utils import RelativePath


class TestWeasyPrint_CustomStyles(WeasyPrintProjectTestCase):
    def _init_project(self) -> Project:
        fs = FakeFileSystem({
            RelativePath('theme/style1.css'): b'''
                h1 { color: lightgreen; }
            ''',
            RelativePath('theme/style2.scss'): b'''
                @mixin red_text { color: indianred; }
                p { @include red_text; }
            ''',
        })

        config = Config(
            pdf=Config_PDF(
                custom_styles=(
                    RelativePath('theme/style1.css'),
                    RelativePath('theme/style2.scss'),
                )))

        return Project(fs, {
            RelativePath(): Volume(config, {
                RelativePath(): Page(dedent('''
                    # Hello, world!
                    The title above should be green.
                    This text should be red.
                ''')),
            })
        })


del WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
