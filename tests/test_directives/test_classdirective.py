import unittest

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from sobiraka.models import Status
from sobiraka.runtime import RT


class TestClassDirective(SinglePageProjectTest):
    REQUIRE = Status.PROCESS3
    SOURCE = '# Test\n\n@class MyClass\n\nThis is a paragraph.'

    def test_paragraph_class(self):
        doc = RT[self.page].doc
        header, para = doc.content  # pylint: disable=unused-variable
        self.assertEqual('MyClass', RT.CLASSES[id(para)])


del SinglePageProjectTest

if __name__ == '__main__':
    unittest.main()
