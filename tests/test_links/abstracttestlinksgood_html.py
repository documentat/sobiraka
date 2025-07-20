from abc import ABCMeta
from dataclasses import replace
from tempfile import TemporaryDirectory
from textwrap import dedent

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeDocument, FakeProject
from sobiraka.models import PageHref, Project, UrlHref
from sobiraka.processing.web import WebBuilder
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath


class AbstractTestLinksGoodHtml(ProjectTestCase, metaclass=ABCMeta):
    SOURCES: dict[str, str]

    def _init_builder(self):
        # pylint: disable=consider-using-with
        output = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        return WebBuilder(self.project, AbsolutePath(output))

    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeDocument({
                k: dedent(v).strip()
                for k, v in self.SOURCES.items()
            }),
        })

    async def asyncSetUp(self):
        await super().asyncSetUp()
        _, self.document0, _, self.document1, _, self.document2, self.document3, _, self.document4 \
            = self.project.get_document().root.all_pages()

    def test_links(self):
        data = {
            self.document0: {
                UrlHref('https://example.com/'): 'https://example.com/',
                PageHref(self.document1): 'sub/document1.html',
                PageHref(self.document2): 'sub/subsub/document2.html',
                PageHref(self.document3): 'sub/subsub/document3.html',
                PageHref(self.document3, 'sect1'): 'sub/subsub/document3.html#sect1',
                PageHref(self.document3, 'section-2'): 'sub/subsub/document3.html#section-2',
                PageHref(self.document4): 'sub/subsub/subsubsub/document4.html',
            },
            self.document1: {
                PageHref(self.document0): '../document0.html',
                PageHref(self.document2): 'subsub/document2.html',
                PageHref(self.document3): 'subsub/document3.html',
                PageHref(self.document4): 'subsub/subsubsub/document4.html',
            },
            self.document2: {
                PageHref(self.document0): '../../document0.html',
                PageHref(self.document1): '../document1.html',
                PageHref(self.document3): 'document3.html',
                PageHref(self.document4): 'subsubsub/document4.html',
            },
            self.document3: {
                PageHref(self.document0): '../../document0.html',
                PageHref(self.document1): '../document1.html',
                PageHref(self.document2): 'document2.html',
                PageHref(self.document3, 'sect1'): '#sect1',
                PageHref(self.document3, 'section-2'): '#section-2',
                PageHref(self.document4): 'subsubsub/document4.html',
            },
            self.document4: {
                PageHref(self.document0): '../../../document0.html',
                PageHref(self.document1): '../../document1.html',
                PageHref(self.document2): '../document2.html',
                PageHref(self.document3): '../document3.html',
            },
        }
        for page, expected_links in data.items():
            with self.subTest(page):
                actual = tuple(replace(link, default_label=None)
                               if isinstance(link, PageHref)
                               else link
                               for link in sorted(RT[page].links))
                self.assertSequenceEqual(tuple(expected_links.keys()), actual)

            for href, expected_url in expected_links.items():
                if isinstance(href, PageHref):
                    with self.subTest(f'{page.location} → {href.target.location}'
                                      + (f'#{href.anchor}' if href.anchor else '')):
                        actual_url = self.builder.make_internal_url(href, page=page)
                        self.assertEqual(expected_url, actual_url)
