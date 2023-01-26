from typing import Any
from unittest import main

from booktestcase import BookTestCase
from sobiraka.models import Href, Page, PageHref, UnknownPageHref, UrlHref
from sobiraka.models.error import BadLinkError, ProcessingError


class TestLinksBad(BookTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.document0, self.document1, self.document2, self.document3, self.document4 = self.book.pages

    def test_ids(self):
        ids = tuple(page.id for page in self.book.pages)
        self.assertSequenceEqual(ids, (
            '--document0',
            '--sub--document1',
            '--sub--subsub--document2',
            '--sub--subsub--document3',
            '--sub--subsub--subsubsub--document4',
        ))

    def test_errors(self):
        data: dict[Page, tuple[ProcessingError, ...]] = {
            self.document0: (
                BadLinkError('../sub/document1.rst'),
                BadLinkError('document2.rst'),
                BadLinkError('sub/subsub/document3.rst#section-1'),
                BadLinkError('sub/subsub/document3.rst#section2'),
                BadLinkError('sub/subsub/subsubsub/document4'),
            ),
            self.document1: (),
            self.document2: (),
            self.document3: (),
            self.document4: (),
        }
        for page, expected_errors in data.items():
            with self.subTest(page):
                self.assertEqual(self.processor.errors[page], set(expected_errors))

    def test_links(self):
        data: dict[Page, tuple[Href, ...]] = {
            self.document0: (
                UnknownPageHref('../sub/document1.rst'),
                UnknownPageHref('document2.rst'),
                PageHref(self.document3),
                PageHref(self.document3, 'section-1'),
                PageHref(self.document3, 'section2'),
                UnknownPageHref('sub/subsub/subsubsub/document4'),
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

if __name__ == '__main__':
    main()
