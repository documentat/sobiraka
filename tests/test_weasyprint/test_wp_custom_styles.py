from unittest import main

from typing_extensions import override

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from helpers.fakefilesystem import PseudoFiles
from sobiraka.models.config import Config, Config_PDF, Config_Paths
from sobiraka.utils import RelativePath


class TestWeasyPrint_CustomStyles(SinglePageProjectTest, WeasyPrintProjectTestCase):
    SOURCE = '''
        # Hello, world!
        The title above should be green.
        This text should be red.
    '''

    @override
    def additional_files(self) -> PseudoFiles:
        return {
            'theme/style1.css': b'''
                h1 { color: lightgreen; }
            ''',
            'theme/style2.scss': b'''
                @mixin red_text { color: indianred; }
                p { @include red_text; }
            ''',
        }

    @override
    def _init_config(self) -> Config:
        return Config(
            paths=Config_Paths(
                root=RelativePath('src'),
            ),
            pdf=Config_PDF(
                custom_styles=(
                    RelativePath('theme/style1.css'),
                    RelativePath('theme/style2.scss'),
                )))


del SinglePageProjectTest, WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
