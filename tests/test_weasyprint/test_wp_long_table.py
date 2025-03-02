from unittest import main

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase

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


del SinglePageProjectTest, WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
