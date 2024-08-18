from unittest import main

from abstracttests.projectdirtestcase import ProjectDirTestCase
from sobiraka.models import DirPage, IndexPage, Page
from sobiraka.utils import RelativePath


class TestChildren(ProjectDirTestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.index_root = self.project.pages_by_path[RelativePath('src')]
        self.document1 = self.project.pages_by_path[RelativePath('src') / 'document1.rst']
        self.index_sub = self.project.pages_by_path[RelativePath('src') / 'sub' / '0-index.rst']
        self.document2 = self.project.pages_by_path[RelativePath('src') / 'sub' / 'document2.rst']
        self.index_subsub = self.project.pages_by_path[RelativePath('src') / 'sub' / 'subsub']
        self.document3 = self.project.pages_by_path[RelativePath('src') / 'sub' / 'subsub' / 'document3.rst']
        self.document4 = self.project.pages_by_path[RelativePath('src') / 'sub' / 'subsub' / 'document4.rst']
        self.document5 = self.project.pages_by_path[RelativePath('src') / 'sub' / 'subsub' / 'document5.rst']

    def test_types(self):
        data: dict[Page, type[Page]] = {
            self.index_root: DirPage,
            self.document1: Page,
            self.index_sub: IndexPage,
            self.document2: Page,
            self.index_subsub: DirPage,
            self.document3: Page,
            self.document4: Page,
            self.document5: Page,
        }
        for page, expected in data.items():
            with self.subTest(page):
                self.assertEqual(expected, type(page))

    def test_breadcrumbs(self):
        data: tuple[tuple[Page, ...], ...] = (
            (self.index_root,),
            (self.index_root, self.document1),
            (self.index_root, self.index_sub),
            (self.index_root, self.index_sub, self.document2),
            (self.index_root, self.index_sub, self.index_subsub),
            (self.index_root, self.index_sub, self.index_subsub, self.document3),
            (self.index_root, self.index_sub, self.index_subsub, self.document4),
            (self.index_root, self.index_sub, self.index_subsub, self.document5),
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
        data: dict[Page, tuple[Page, ...]] = {
            self.index_root: (self.document1, self.index_sub),
            self.document1: (),
            self.index_sub: (self.document2, self.index_subsub),
            self.document2: (),
            self.index_subsub: (self.document3, self.document4, self.document5),
            self.document3: (),
            self.document4: (),
            self.document5: (),
        }
        for page, expected in data.items():
            with self.subTest(page):
                self.assertEqual(expected, page.children)


del ProjectDirTestCase

if __name__ == '__main__':
    main()
