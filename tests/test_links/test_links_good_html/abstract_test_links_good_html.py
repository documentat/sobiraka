from abstracttests.booktestcase import BookTestCase
from sobiraka.models import Href, Page, PageHref, UrlHref
from sobiraka.processing import HtmlBuilder


class AbstractTestLinksGoodHtml(BookTestCase):
    def _init_processor(self):
        return HtmlBuilder(self.book)

    async def asyncSetUp(self):
        await super().asyncSetUp()
        _, self.document0, _, self.document1, _, self.document2, self.document3, _, self.document4 = self.book.pages

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
        actual_ids = tuple(page.id for page in self.book.pages)
        self.assertSequenceEqual(expected_ids, actual_ids)

    def test_links(self):
        data: dict[Page, dict[Href, str]] = {
            self.document0: {
                PageHref(self.document1): 'sub/document1.html',
                PageHref(self.document2): 'sub/subsub/document2.html',
                PageHref(self.document3): 'sub/subsub/document3.html',
                PageHref(self.document3, 'sect1'): 'sub/subsub/document3.html#sect1',
                PageHref(self.document3, 'section-2'): 'sub/subsub/document3.html#section-2',
                PageHref(self.document4): 'sub/subsub/subsubsub/document4.html',
                UrlHref('https://example.com/'): 'https://example.com/',
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
                PageHref(self.document4): 'subsubsub/document4.html',
                PageHref(self.document3, 'section-2'): '#section-2',
                PageHref(self.document3, 'sect1'): '#sect1',
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
                self.assertSequenceEqual(tuple(expected_links.keys()), tuple(self.processor.links[page]))
            for href, expected_url in expected_links.items():
                if isinstance(href, PageHref):
                    with self.subTest(
                            str(page.relative_path.with_suffix(''))
                            + ' → '
                            + str(href.target.relative_path.with_suffix(''))
                            + (f'#{href.anchor}' if href.anchor else '')
                    ):
                        actual_url = self.processor.make_internal_url(href, page=page)
                        self.assertEqual(expected_url, actual_url)


del BookTestCase
