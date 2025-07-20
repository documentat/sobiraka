from abc import ABCMeta
from textwrap import dedent
from typing import Generic, Sequence, TypeVar

from typing_extensions import override

from helpers.fakefilesystem import PseudoFiles
from helpers.fakeproject import FakeDocument, FakeProject
from sobiraka.models import Document, Page, Project
from sobiraka.models.config import Config, Config_Paths
from sobiraka.processing.abstract import Builder
from sobiraka.utils import RelativePath
from .projecttestcase import ProjectTestCase

T = TypeVar('T', bound=Builder)


class SinglePageProjectTest(ProjectTestCase, Generic[T], metaclass=ABCMeta):
    PATH = 'index.md'
    LOCATION = '/'
    SOURCE: str
    EXPECTED_ISSUES: Sequence[str] = ()

    @override
    def _init_project(self) -> Project:
        project = FakeProject({
            'src': FakeDocument(self._init_config(), {
                self.PATH: dedent(self.SOURCE).strip(),
            }),
        })
        project.fs.add_files(self.additional_files())
        return project

    def _init_config(self) -> Config:
        return Config(paths=Config_Paths(root=RelativePath('src')))

    def additional_files(self) -> PseudoFiles:
        return {}

    @property
    def document(self) -> Document:
        return self.project.get_document()

    @property
    def page(self) -> Page:
        return self.document.get_page_by_location(self.LOCATION)

    @override
    async def _process(self):
        # pylint: disable=broad-exception-caught
        try:
            await super()._process()
        except* Exception as eg:
            self.exceptions = eg

    def test_issues(self):
        page, = self.project.get_document().root.pages

        expected = '\n'.join(self.EXPECTED_ISSUES) + '\n'
        actual = '\n'.join(map(str, page.issues)) + '\n'
        self.assertEqual(expected, actual)
