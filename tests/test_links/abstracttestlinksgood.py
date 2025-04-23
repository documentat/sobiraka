from abc import ABCMeta
from dataclasses import replace
from textwrap import dedent

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import PageHref, Project, UrlHref
from sobiraka.runtime import RT


class AbstractTestLinksGood(ProjectTestCase, metaclass=ABCMeta):
    SOURCES: dict[str, str]

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

    def test_links(self):
        data = {
            self.document0: (
                UrlHref('https://example.com/'),
                PageHref(self.document1),
                PageHref(self.document2),
                PageHref(self.document3),
                PageHref(self.document3, 'sect1'),
                PageHref(self.document3, 'section-2'),
                PageHref(self.document4),
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
