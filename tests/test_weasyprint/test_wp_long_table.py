from unittest import main
from unittest.mock import Mock

from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from sobiraka.models import FileSystem, Page, Project, Volume
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


class TestWeasyPrint_LongTable(WeasyPrintProjectTestCase):
    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            RelativePath(): Volume({
                RelativePath(): Page(SOURCE),
            }),
        })


del WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
