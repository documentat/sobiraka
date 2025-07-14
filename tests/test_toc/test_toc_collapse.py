import unittest
from math import inf

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project
from sobiraka.models.config import CombinedToc
from sobiraka.processing.toc import toc


class TestTocCollapse(ProjectTestCase):
    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                '_nav.yaml': '''
                    items:
                      - not collapsed
                      - collapsed via nav meta:
                          toc_collapse: true
                      - collapsed via page meta
                ''',
                'not collapsed': {'index': '', 'subpage': ''},
                'collapsed via nav meta': {'index': '', 'subpage': ''},
                'collapsed via page meta': {'index': '---\ntoc_collapse: true\n---', 'subpage': ''},
            })
        })

    def test_collapsed(self):
        data = {
            'not collapsed': False,
            'collapsed via nav meta': True,
            'collapsed via page meta': True,
        }

        items = toc(self.project.get_volume().root_page,
                    builder=self.builder,
                    toc_depth=inf,
                    combined_toc=CombinedToc.ALWAYS)

        for item in items:
            with self.subTest(item.title):
                self.assertEqual(data[item.title], item.is_collapsed)


if __name__ == '__main__':
    unittest.main()
