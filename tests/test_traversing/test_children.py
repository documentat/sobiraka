from unittest import main

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Page, Project


class TestChildren(ProjectTestCase):
    # pylint: disable=too-many-instance-attributes

    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                'document1.md': '# Document 1',
                'sub': {
                    '0-index.md': '# Sub',
                    'document2.md': '# Document 2',
                    'subsub': {
                        'document3.md': '# Document 3',
                        'document4.md': '# Document 4',
                        'document5.md': '# Document 5',
                    },
                },
            })
        })

    async def _process(self):
        await super()._process()
        volume = self.project.get_volume()

        self.index_root = volume.root_page
        self.document1 = volume.get_page_by_location('/document1')
        self.index_sub = volume.get_page_by_location('/sub/')
        self.document2 = volume.get_page_by_location('/sub/document2')
        self.index_subsub = volume.get_page_by_location('/sub/subsub/')
        self.document3 = volume.get_page_by_location('/sub/subsub/document3')
        self.document4 = volume.get_page_by_location('/sub/subsub/document4')
        self.document5 = volume.get_page_by_location('/sub/subsub/document5')

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
        data = {
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


del ProjectTestCase

if __name__ == '__main__':
    main()
