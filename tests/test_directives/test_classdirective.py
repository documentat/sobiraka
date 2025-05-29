import unittest

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from sobiraka.models import Status
from sobiraka.runtime import RT


class TestClassDirective(SinglePageProjectTest):
    REQUIRE = Status.NUMERATE
    SOURCE = '# Test\n\n@class MyClass\n\nThis is a paragraph.'

    def test_paragraph_class(self):
        _, para = RT[self.page].doc.content
        self.assertEqual('MyClass', RT.CLASSES[id(para)])


del SinglePageProjectTest

if __name__ == '__main__':
    unittest.main()
