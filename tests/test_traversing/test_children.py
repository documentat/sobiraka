from unittest import main
from unittest.mock import Mock

from abstracttests.projecttestcase import ProjectTestCase
from sobiraka.models import DirPage, FileSystem, IndexPage, Page, Project, Volume
from sobiraka.utils import RelativePath


class TestChildren(ProjectTestCase):
    def _init_project(self) -> Project:
        self.index_root = DirPage()
        self.document1 = Page('# Document 1')
        self.index_sub = IndexPage('# Sub')
        self.document2 = Page('# Document 2')
        self.index_subsub = Page()
        self.document3 = Page('# Document 3')
        self.document4 = Page('# Document 4')
        self.document5 = Page('# Document 5')

        return Project(Mock(FileSystem), {
            RelativePath('src'): Volume({
                RelativePath(): self.index_root,
                RelativePath() / 'document1.md': self.document1,
                RelativePath() / 'sub' / '0-index.md': self.index_sub,
                RelativePath() / 'sub' / 'document2.md': self.document2,
                RelativePath() / 'sub' / 'subsub': self.index_subsub,
                RelativePath() / 'sub' / 'subsub' / 'document3.md': self.document3,
                RelativePath() / 'sub' / 'subsub' / 'document4.md': self.document4,
                RelativePath() / 'sub' / 'subsub' / 'document5.md': self.document5,
            })
        })

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


del ProjectTestCase

if __name__ == '__main__':
    main()
