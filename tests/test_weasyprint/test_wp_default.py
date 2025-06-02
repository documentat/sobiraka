from unittest import main

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from sobiraka.models.config import Config, Config_Paths
from sobiraka.utils import RelativePath

SOURCE = '''
# Hello, world!

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur sit amet aliquam quam. Fusce tellus erat, ullamcorper at aliquet sed, ornare molestie sem. Maecenas consequat nec metus id dapibus. Proin vulputate venenatis egestas.

## Section 1
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur sit amet aliquam quam. Fusce tellus erat, ullamcorper at aliquet sed, ornare molestie sem. Maecenas consequat nec metus id dapibus. Proin vulputate venenatis egestas.

## Section 2
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur sit amet aliquam quam. Fusce tellus erat, ullamcorper at aliquet sed, ornare molestie sem. Maecenas consequat nec metus id dapibus. Proin vulputate venenatis egestas.

## Section 3
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur sit amet aliquam quam. Fusce tellus erat, ullamcorper at aliquet sed, ornare molestie sem. Maecenas consequat nec metus id dapibus. Proin vulputate venenatis egestas.

## Section 4
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur sit amet aliquam quam. Fusce tellus erat, ullamcorper at aliquet sed, ornare molestie sem. Maecenas consequat nec metus id dapibus. Proin vulputate venenatis egestas.

## Section 5
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur sit amet aliquam quam. Fusce tellus erat, ullamcorper at aliquet sed, ornare molestie sem. Maecenas consequat nec metus id dapibus. Proin vulputate venenatis egestas.
'''


class TestWeasyPrint_Default(SinglePageProjectTest, WeasyPrintProjectTestCase):
    SOURCE = SOURCE

    def _init_config(self) -> Config:
        return Config(
            paths=Config_Paths(
                root=RelativePath('src'),
            ),
            title='Example',
            variables=dict(
                COVER_TOP='Top Text',
                COVER_BOTTOM='Bottom Text',
            )
        )


del SinglePageProjectTest, WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
