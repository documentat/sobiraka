import unittest

from abstracttests.projecttestcase import FailingProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project, Status
from sobiraka.processing.abstract.waiter import IssuesOccurred
from sobiraka.processing.directive import InvalidDirectiveArguments, UnknownDirective


class TestInvalidDirective(FailingProjectTestCase):
    REQUIRE = Status.NUMERATE
    EXPECTED_EXCEPTION_TYPES = {IssuesOccurred}

    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                'index.md': '@haha --lol\n\n@toc --haha --lol',
            }),
        })

    def test_issues(self):
        page = self.project.get_volume().root_page

        expected = [UnknownDirective('@haha'), InvalidDirectiveArguments('@toc')]
        self.assertEqual(expected, page.issues)


del FailingProjectTestCase

if __name__ == '__main__':
    unittest.main()
