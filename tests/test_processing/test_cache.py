# from contextlib import contextmanager
# from pathlib import Path
# from tempfile import TemporaryDirectory
# from typing import ContextManager
from unittest import IsolatedAsyncioTestCase, SkipTest, main, skip
# from unittest.mock import Mock, call
#
# from sobiraka.cache import init_cache
# from sobiraka.models import FileSystem, Page, Project, Volume
# from sobiraka.processing.abstract import Processor, ProjectProcessor


class TestCache(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        raise SkipTest('Cache does not work')
    #     cache_dir = Path(self.enterContext(TemporaryDirectory(prefix='sobiraka-test-')))
    #     init_cache(cache_dir)
    #
    #     self.project = Project(Mock(FileSystem), {
    #         Path(''): Volume({
    #             Path('page1.md'): Page('# Page 1'),
    #             Path('page2.md'): Page('# Page 2'),
    #             Path('page3.md'): Page('# Page 3'),
    #         }),
    #     })
    #
    # @contextmanager
    # def subTestWithProcessor(self, message: str) -> ContextManager[Processor]:
    #     processor = ProjectProcessor(self.project)
    #     processor.process_container = Mock(wraps=processor.process_container)
    #     with self.subTest(message):
    #         yield processor
    #
    # async def test_cache(self):
    #     _, page1, page2, page3 = self.project.pages
    #
    #     with self.subTestWithProcessor('no cache') as processor:
    #         await processor.process2(page1)
    #         await processor.process2(page2)
    #         await processor.process2(page3)
    #
    #         self.assertEqual(3, processor.process_container.call_count)
    #
    #     with self.subTestWithProcessor('all from cache') as processor:
    #         await processor.process2(page1)
    #         await processor.process2(page2)
    #         await processor.process2(page3)
    #
    #         self.assertEqual(0, processor.process_container.call_count)
    #
    #     with self.subTestWithProcessor('modify page1') as processor:
    #         processor.process2_tasks = Mock(__getitem__=Mock(return_value=[]))
    #
    #         page1._process_raw('# Page 1\n\nmodified')
    #
    #         await processor.process2(page1)
    #         await processor.process2(page2)
    #         await processor.process2(page3)
    #
    #         self.assertIn(call.__getitem__(page1), processor.process2_tasks.mock_calls)
    #         self.assertNotIn(call.__getitem__(page2), processor.process2_tasks.mock_calls)
    #         self.assertNotIn(call.__getitem__(page3), processor.process2_tasks.mock_calls)
    #
    #     with self.subTestWithProcessor('page2 depends on page1') as processor:
    #         processor.process2_tasks = Mock(__getitem__=Mock(return_value=[]))
    #
    #         page2._process_raw(page2.text + '\n\n[link](page1.md)')
    #
    #         await processor.process2(page1)
    #         await processor.process2(page2)
    #         await processor.process2(page3)
    #
    #         self.assertNotIn(call.__getitem__(page1), processor.process2_tasks.mock_calls)
    #         self.assertIn(call.__getitem__(page2), processor.process2_tasks.mock_calls)
    #         self.assertNotIn(call.__getitem__(page3), processor.process2_tasks.mock_calls)
    #
    #     with self.subTestWithProcessor('modify page1 again') as processor:
    #         processor.process2_tasks = Mock(__getitem__=Mock(return_value=[]))
    #
    #         page1._process_raw('# Page 1\n\nmodified again')
    #
    #         await processor.process2(page1)
    #         await processor.process2(page2)
    #         await processor.process2(page3)
    #
    #         self.assertIn(call.__getitem__(page1), processor.process2_tasks.mock_calls)
    #         self.assertIn(call.__getitem__(page2), processor.process2_tasks.mock_calls)
    #         self.assertNotIn(call.__getitem__(page3), processor.process2_tasks.mock_calls)
    #
    #     with self.subTestWithProcessor('revert page1') as processor:
    #         processor.process2_tasks = Mock(__getitem__=Mock(return_value=[]))
    #
    #         page1._process_raw('# Page 1')
    #
    #         await processor.process2(page1)
    #         await processor.process2(page2)
    #         await processor.process2(page3)
    #
    #         self.assertNotIn(call.__getitem__(page1), processor.process2_tasks.mock_calls)
    #         self.assertIn(call.__getitem__(page2), processor.process2_tasks.mock_calls)
    #         self.assertNotIn(call.__getitem__(page3), processor.process2_tasks.mock_calls)
    #
    #     with self.subTestWithProcessor('revert page2') as processor:
    #         processor.process2_tasks = Mock(__getitem__=Mock(return_value=[]))
    #
    #         page2._process_raw('# Page 2')
    #
    #         await processor.process2(page1)
    #         await processor.process2(page2)
    #         await processor.process2(page3)
    #
    #         self.assertNotIn(call.__getitem__(page1), processor.process2_tasks.mock_calls)
    #         self.assertNotIn(call.__getitem__(page2), processor.process2_tasks.mock_calls)
    #         self.assertNotIn(call.__getitem__(page3), processor.process2_tasks.mock_calls)

if __name__ == '__main__':
    main()