from abc import ABCMeta
from textwrap import dedent
from typing import TypeVar
from unittest.mock import Mock

from typing_extensions import Generic, Sequence, final, override

from sobiraka.models import FileSystem, IndexPage, Project, Volume
from sobiraka.models.config import Config
from sobiraka.processing.abstract import Builder
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath
from .projecttestcase import ProjectTestCase

T = TypeVar('T', bound=Builder)


class SinglePageProjectTest(ProjectTestCase, Generic[T], metaclass=ABCMeta):
    PATH = RelativePath()
    SOURCE: str
    EXPECTED_ISSUES: Sequence[str] = ()

    @override
    def _init_project(self) -> Project:
        self.page = IndexPage(dedent(self.SOURCE).strip())

        self.volume = Volume(self._init_config(), {
            self.PATH: self.page,
        })

        return Project(self._init_filesystem(), {
            RelativePath('src'): self.volume,
        })

    def _init_config(self) -> Config:
        return Config()

    def _init_filesystem(self) -> FileSystem:
        return Mock(FileSystem)

    @final
    @override
    async def _process(self):
        try:
            await super()._process()
        except* Exception as eg:
            self.exceptions = eg

    def test_issues(self):
        expected = '\n'.join(self.EXPECTED_ISSUES) + '\n'
        actual = '\n'.join(map(str, RT[self.page].issues)) + '\n'
        self.assertEqual(expected, actual)
