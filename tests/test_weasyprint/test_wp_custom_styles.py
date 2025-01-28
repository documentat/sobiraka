from unittest import main

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from helpers import FakeFileSystem
from sobiraka.models import FileSystem
from sobiraka.models.config import Config, Config_PDF
from sobiraka.utils import RelativePath


class TestWeasyPrint_CustomStyles(SinglePageProjectTest, WeasyPrintProjectTestCase):
    SOURCE = '''
        # Hello, world!
        The title above should be green.
        This text should be red.
    '''

    def _init_filesystem(self) -> FileSystem:
        return FakeFileSystem({
            RelativePath('theme/style1.css'): b'''
                h1 { color: lightgreen; }
            ''',
            RelativePath('theme/style2.scss'): b'''
                @mixin red_text { color: indianred; }
                p { @include red_text; }
            ''',
        })

    def _init_config(self) -> Config:
        return Config(
            pdf=Config_PDF(
                custom_styles=(
                    RelativePath('theme/style1.css'),
                    RelativePath('theme/style2.scss'),
                )))


del SinglePageProjectTest, WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
