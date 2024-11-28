from unittest.mock import Mock

from abstracttests.projecttestcase import ProjectTestCase
from sobiraka.models import FileSystem, Page, PageStatus, Project, Volume
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath


class TestClassDirective(ProjectTestCase):
    REQUIRE = PageStatus.PROCESS1

    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            RelativePath('src'): Volume({
                RelativePath(): Page('# Test\n\n@class MyClass\n\nThis is a paragraph.'),
            }),
        })

    def test_paragraph_class(self):
        doc = RT[self.project.pages[0]].doc
        header, directive, para = doc.content
        self.assertEqual('MyClass', RT.CLASSES[id(para)])
