from abc import ABCMeta
from textwrap import dedent
from typing import Generic, Sequence, TypeVar

from more_itertools.more import last
from typing_extensions import override

from helpers.fakefilesystem import PseudoFiles
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project
from sobiraka.models.config import Config, Config_Paths
from sobiraka.processing.abstract import Builder
from sobiraka.utils import RelativePath
from .projecttestcase import ProjectTestCase

T = TypeVar('T', bound=Builder)


class SinglePageProjectTest(ProjectTestCase, Generic[T], metaclass=ABCMeta):
    PATH = 'index.md'
    SOURCE: str
    EXPECTED_ISSUES: Sequence[str] = ()

    @override
    def _init_project(self) -> Project:
        project = FakeProject({
            'src': FakeVolume(self._init_config(), {
                self.PATH: dedent(self.SOURCE).strip(),
            }),
        })
        project.fs.add_files(self.additional_files())
        return project

    def _init_config(self) -> Config:
        return Config(paths=Config_Paths(root=RelativePath('src')))

    def additional_files(self) -> PseudoFiles:
        return {}

    @override
    async def _process(self):
        # pylint: disable=broad-exception-caught
        try:
            await super()._process()
            self.page = last(self.project.get_volume().root.all_pages())
        except* Exception as eg:
            self.exceptions = eg

    def test_issues(self):
        page, = self.project.get_volume().root.pages

        expected = '\n'.join(self.EXPECTED_ISSUES) + '\n'
        actual = '\n'.join(map(str, page.issues)) + '\n'
        self.assertEqual(expected, actual)
