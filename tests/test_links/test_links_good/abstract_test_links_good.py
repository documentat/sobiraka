from abstracttests.booktestcase import BookTestCase
from sobiraka.models import Href, Page, PageHref, UrlHref


class AbstractTestLinksGood(BookTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        _, self.document0, _, self.document1, _, self.document2, self.document3, _, self.document4 = self.book.pages

    def test_ids(self):
        ids = tuple(page.id for page in self.book.pages)
        self.assertSequenceEqual(ids, (
            'r',
            'r--document0',
            'r--sub',
            'r--sub--document1',
            'r--sub--subsub',
            'r--sub--subsub--document2',
            'r--sub--subsub--document3',
            'r--sub--subsub--subsubsub',
            'r--sub--subsub--subsubsub--document4',
        ))

    def test_links(self):
        data: dict[Page, tuple[Href, ...]] = {
            self.document0: (
                PageHref(self.document1),
                PageHref(self.document2),
                PageHref(self.document3),
                PageHref(self.document3, 'sect1'),
                PageHref(self.document3, 'section-2'),
                PageHref(self.document4),
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
                self.assertSequenceEqual(tuple(self.processor.links[page]), expected_links)


del BookTestCase
