from unittest import main

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase

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


del SinglePageProjectTest, WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
