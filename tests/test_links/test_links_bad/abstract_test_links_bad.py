from abstracttests.booktestcase import BookTestCase
from sobiraka.models import BadLink, Href, Issue, Page, PageHref, UrlHref


class AbstractTestLinksBad(BookTestCase):
    EXT: str

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

    def test_errors(self):
        data: dict[Page, tuple[Issue, ...]] = {
            self.document0: (
                BadLink(f'../sub/document1.{self.EXT}'),
                BadLink(f'document2.{self.EXT}'),
                BadLink(f'sub/subsub/document3.{self.EXT}#section-1'),
                BadLink(f'sub/subsub/document3.{self.EXT}#section2'),
                BadLink('sub/subsub/subsubsub/document4'),
            ),
            self.document1: (),
            self.document2: (),
            self.document3: (),
            self.document4: (),
        }
        for page, expected_errors in data.items():
            with self.subTest(page):
                self.assertEqual(set(expected_errors), self.processor.issues[page])

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
                self.assertSequenceEqual(expected_links, tuple(self.processor.links[page]))


del BookTestCase