from unittest import main
from unittest.mock import Mock

from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from sobiraka.models import FileSystem, Page, Project, Volume
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


class TestWeasyPrint_Default(WeasyPrintProjectTestCase):
    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            RelativePath(): Volume({
                RelativePath(): Page(SOURCE),
            }),
        })


del WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
