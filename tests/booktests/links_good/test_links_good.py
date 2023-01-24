from unittest import main

from booktestcase import BookTestCase
from sobiraka.models import Href, Page, PageHref, UrlHref


class TestLinksGood(BookTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.document0, self.document1, self.document2, self.document3, self.document4 = self.book.pages

    def test_ids(self):
        ids = tuple(page.id for page in self.book.pages)
        self.assertSequenceEqual(ids, (
            'document0',
            'sub--document1',
            'sub--subsub--document2',
            'sub--subsub--document3',
            'sub--subsub--subsubsub--document4',
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
                self.assertSequenceEqual(tuple(page.links), expected_links)


del BookTestCase

if __name__ == '__main__':
    main()
