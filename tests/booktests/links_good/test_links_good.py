from functools import cached_property
from itertools import product
from pathlib import Path
from textwrap import dedent
from unittest import main

from booktestcase import BookTestCase
from sobiraka.models import Page, PageHref, Href


class TestLinks(BookTestCase):
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

    # def test_links(self):
    #     data: dict[Page, tuple[Href, ...]] = {
    #         self.document0: (
    #             PageHref(self.document1),
    #             PageHref(self.document2),
    #             PageHref(self.document3),
    #             PageHref(self.document3, 'sect1'),
    #             PageHref(self.document3, 'section-2'),
    #             PageHref(self.document4),
    #         ),
    #         self.document1: (
    #             PageHref(self.document0),
    #             PageHref(self.document2),
    #             PageHref(self.document3),
    #             PageHref(self.document4),
    #         ),
    #         self.document2: (
    #             PageHref(self.document0),
    #             PageHref(self.document1),
    #             PageHref(self.document3),
    #             PageHref(self.document4),
    #         ),
    #         self.document3: (
    #             PageHref(self.document0),
    #             PageHref(self.document1),
    #             PageHref(self.document2),
    #             PageHref(self.document3, 'sect1'),
    #             PageHref(self.document3, 'section-2'),
    #             PageHref(self.document4),
    #         ),
    #         self.document4: (
    #             PageHref(self.document0),
    #             PageHref(self.document1),
    #             PageHref(self.document2),
    #             PageHref(self.document3),
    #         ),
    #     }
    #     for page, expected_links in data.items():
    #         with self.subTest(page.relative_path.with_suffix('')):
    #             links = sorted(page.links, key=lambda href: (href.__class__.__name__, str(href)))
    #             self.assertSequenceEqual(links, expected_links)


del BookTestCase

if __name__ == '__main__':
    main()
