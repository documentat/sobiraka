from pathlib import Path
from unittest import main

from abstracttests.booktestcase import BookTestCase
from sobiraka.models import EmptyPage, Page


class TestChildren(BookTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.index_root = self.project.pages_by_path[Path()]
        self.document1 = self.project.pages_by_path[Path() / 'document1.rst']
        self.index_sub = self.project.pages_by_path[Path() / 'sub' / '0-index.rst']
        self.document2 = self.project.pages_by_path[Path() / 'sub' / 'document2.rst']
        self.index_subsub = self.project.pages_by_path[Path() / 'sub' / 'subsub']
        self.document3 = self.project.pages_by_path[Path() / 'sub' / 'subsub' / 'document3.rst']
        self.document4 = self.project.pages_by_path[Path() / 'sub' / 'subsub' / 'document4.rst']
        self.document5 = self.project.pages_by_path[Path() / 'sub' / 'subsub' / 'document5.rst']

    def test_types(self):
        data: dict[Page, type[Page]] = {
            self.index_root: EmptyPage,
            self.document1: Page,
            self.index_sub: Page,
            self.document2: Page,
            self.index_subsub: EmptyPage,
            self.document3: Page,
            self.document4: Page,
            self.document5: Page,
        }
        for page, expected in data.items():
            with self.subTest(page):
                self.assertEqual(expected, type(page))

    def test_is_index(self):
        data: dict[Page, bool] = {
            self.index_root: True,
            self.document1: False,
            self.index_sub: True,
            self.document2: False,
            self.index_subsub: True,
            self.document3: False,
            self.document4: False,
            self.document5: False,
        }
        for page, expected in data.items():
            with self.subTest(page):
                self.assertEqual(expected, page.is_index)

    def test_breadcrumbs(self):
        data: tuple[list[Page], ...] = (
            [self.index_root],
            [self.index_root, self.document1],
            [self.index_root, self.index_sub],
            [self.index_root, self.index_sub, self.document2],
            [self.index_root, self.index_sub, self.index_subsub],
            [self.index_root, self.index_sub, self.index_subsub, self.document3],
            [self.index_root, self.index_sub, self.index_subsub, self.document4],
            [self.index_root, self.index_sub, self.index_subsub, self.document5],
        )
        for expected in data:
            page = expected[-1]
            with self.subTest(page):
                self.assertSequenceEqual(expected, page.breadcrumbs)

    def test_parent(self):
        data: dict[Page, Page] = {
            self.index_root: None,
            self.document1: self.index_root,
            self.index_sub: self.index_root,
            self.document2: self.index_sub,
            self.index_subsub: self.index_sub,
            self.document3: self.index_subsub,
            self.document4: self.index_subsub,
            self.document5: self.index_subsub,
        }
        for page, expected in data.items():
            with self.subTest(page):
                self.assertEqual(expected, page.parent)

    def test_children(self):
        data: dict[Page, list[Page]] = {
            self.index_root: [self.document1, self.index_sub],
            self.document1: [],
            self.index_sub: [self.document2, self.index_subsub],
            self.document2: [],
            self.index_subsub: [self.document3, self.document4, self.document5],
            self.document3: [],
            self.document4: [],
            self.document5: [],
        }
        for page, expected in data.items():
            with self.subTest(page):
                self.assertEqual(expected, page.children)

    def test_children_recursive(self):
        data: dict[Page, list[Page]] = {
            self.index_root: [self.document1, self.index_sub, self.document2, self.index_subsub, self.document3, self.document4, self.document5],
            self.document1: [],
            self.index_sub: [self.document2, self.index_subsub, self.document3, self.document4, self.document5],
            self.document2: [],
            self.index_subsub: [self.document3, self.document4, self.document5],
            self.document3: [],
            self.document4: [],
            self.document5: [],
        }
        for page, expected in data.items():
            with self.subTest(page):
                self.assertEqual(expected, page.children_recursive)


del BookTestCase

if __name__ == '__main__':
    main()
