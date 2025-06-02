from unittest import main

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from sobiraka.models.config import Config, Config_Paths
from sobiraka.utils import RelativePath

SOURCE = '''
# Hello, world!

+------------------------------+------------------------------+------------------------------+
| Column A                     | Column B                     | Column C                     |
+==============================+==============================+==============================+
'''.rstrip()

SOURCE += 20 * '''
| Lorem ipsum dolor sit amet,  | Lorem ipsum dolor sit amet,  | Lorem ipsum dolor sit amet,  |
| consectetur adipiscing elit. | consectetur adipiscing elit. | consectetur adipiscing elit. |
| Curabitur sit amet aliquam   | Curabitur sit amet aliquam   | Curabitur sit amet aliquam   |
| quam.                        | quam.                        | quam.                        |
+------------------------------+------------------------------+------------------------------+
'''.rstrip()


class TestWeasyPrint_LongTable(SinglePageProjectTest, WeasyPrintProjectTestCase):
    SOURCE = SOURCE

    def _init_config(self) -> Config:
        return Config(
            paths=Config_Paths(root=RelativePath('src')),
            variables=dict(NOCOVER=True),
        )


del SinglePageProjectTest, WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
