from abc import ABCMeta
from dataclasses import replace
from textwrap import dedent

from abstracttests.projecttestcase import FailingProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Href, Page, PageHref, Project, UrlHref
from sobiraka.models.issues import BadLink, Issue
from sobiraka.processing.abstract.waiter import IssuesOccurred
from sobiraka.runtime import RT


class AbstractTestLinksBad(FailingProjectTestCase, metaclass=ABCMeta):
    SOURCES: dict[str, str]
    EXT: str

    EXPECTED_EXCEPTION_TYPES = {IssuesOccurred}

    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                k: dedent(v).strip()
                for k, v in self.SOURCES.items()
            }),
        })

    async def asyncSetUp(self):
        await super().asyncSetUp()
        volume = self.project.get_volume()

        self.document0 = volume.get_page_by_location('/document0')
        self.document1 = volume.get_page_by_location('/sub/document1')
        self.document2 = volume.get_page_by_location('/sub/subsub/document2')
        self.document3 = volume.get_page_by_location('/sub/subsub/document3')
        self.document4 = volume.get_page_by_location('/sub/subsub/subsubsub/document4')

    def test_issues(self):
        data: dict[Page, list[Issue]] = {
            self.document0: [
                BadLink(f'../sub/document1.{self.EXT}'),
                BadLink(f'document2.{self.EXT}'),
                BadLink(f'sub/subsub/document3.{self.EXT}#section-1'),
                BadLink(f'sub/subsub/document3.{self.EXT}#section2'),
                BadLink('sub/subsub/subsubsub/document4'),
            ],
            self.document1: [],
            self.document2: [],
            self.document3: [],
            self.document4: [],
        }
        for page, expected_issues in data.items():
            with self.subTest(page):
                self.assertEqual(expected_issues, sorted(page.issues))

    def test_links(self):
        data: dict[Page, tuple[Href, ...]] = {
            self.document0: (
                UrlHref('https://example.com/'),
                PageHref(self.document3),
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
                PageHref(self.document3, 'sect1'),
                PageHref(self.document3, 'section-2'),
                PageHref(self.document4),
            ),
            self.document4: (
                PageHref(self.document0),
                PageHref(self.document1),
                PageHref(self.document2),
                PageHref(self.document3),
            ),
        }
        for page, expected in data.items():
            with self.subTest(page):
                actual = tuple(replace(link, default_label=None)
                               if isinstance(link, PageHref)
                               else link
                               for link in sorted(RT[page].links))
                self.assertSequenceEqual(expected, actual)
