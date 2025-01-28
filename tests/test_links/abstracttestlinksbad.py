from abc import ABCMeta
from contextlib import suppress
from textwrap import dedent
from unittest.mock import Mock

from abstracttests.projectdirtestcase import ProjectDirTestCase
from abstracttests.projecttestcase import ProjectTestCase
from sobiraka.models import FileSystem, Href, Page, PageHref, Project, UrlHref, Volume
from sobiraka.models.issues import BadLink, Issue
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath


class AbstractTestLinksBad(ProjectTestCase, metaclass=ABCMeta):
    SOURCE: dict[str, str]
    EXT: str

    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            RelativePath('src'): Volume({
                RelativePath(k): Page(dedent(v).strip())
                for k, v in self.SOURCES.items()
            }),
        })

    async def asyncSetUp(self):
        await super().asyncSetUp()
        _, self.document0, _, self.document1, _, self.document2, self.document3, _, self.document4 = self.project.pages

    def test_ids(self):
        expected_ids = (
            'r',
            'r--document0',
            'r--sub',
            'r--sub--document1',
            'r--sub--subsub',
            'r--sub--subsub--document2',
            'r--sub--subsub--document3',
            'r--sub--subsub--subsubsub',
            'r--sub--subsub--subsubsub--document4',
        )
        actual_ids = tuple(page.id for page in self.project.pages)
        self.assertSequenceEqual(expected_ids, actual_ids)

    async def _process(self):
        with suppress(ExceptionGroup):
            await super()._process()

    def test_issues(self):
        data: dict[Page, list[Issue]] = {
            self.document0: [
                BadLink(f'../sub/document1.{self.EXT}'),
                BadLink(f'document2.{self.EXT}'),
                BadLink('sub/subsub/subsubsub/document4'),
                BadLink(f'sub/subsub/document3.{self.EXT}#section-1'),
                BadLink(f'sub/subsub/document3.{self.EXT}#section2'),
            ],
            self.document1: [],
            self.document2: [],
            self.document3: [],
            self.document4: [],
        }
        for page, expected_issues in data.items():
            with self.subTest(page):
                self.assertEqual(expected_issues, RT[page].issues)

    def test_links(self):
        data: dict[Page, tuple[Href, ...]] = {
            self.document0: (
                PageHref(self.document3),
                PageHref(self.document3, 'section-1'),
                PageHref(self.document3, 'section2'),
                UrlHref('https://example.com/'),
            ),
            self.document1: (
                PageHref(self.document0),
                PageHref(self.document2),
                PageHref(self.document3),
                PageHref(self.document4),
            ),
            self.document2: (
                PageHref(self.document0),
                PageHref(self.document1),
                PageHref(self.document3),
                PageHref(self.document4),
            ),
            self.document3: (
                PageHref(self.document0),
                PageHref(self.document1),
                PageHref(self.document2),
                PageHref(self.document4),
                PageHref(self.document3, 'section-2'),
                PageHref(self.document3, 'sect1'),
            ),
            self.document4: (
                PageHref(self.document0),
                PageHref(self.document1),
                PageHref(self.document2),
                PageHref(self.document3),
            ),
        }
        for page, expected_links in data.items():
            with self.subTest(page):
                self.assertSequenceEqual(expected_links, tuple(RT[page].links))


del ProjectDirTestCase
