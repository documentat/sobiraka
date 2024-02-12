from os.path import relpath
from os.path import relpath
from pathlib import Path
from unittest import main
from unittest.mock import Mock

from abstracttests.abstracttestwithrt import AbstractTestWithRtPages, AbstractTestWithRtTmp
from sobiraka.models import FileSystem, Page, PageHref, Project, Volume
from sobiraka.models.config import CombinedToc
from sobiraka.models.toc import Toc, TocItem, toc
from sobiraka.processing.abstract import Processor


class TestCombinedToc(AbstractTestWithRtTmp, AbstractTestWithRtPages):
    async def asyncSetUp(self):
        await super().asyncSetUp()

        self.project = Project(Mock(FileSystem), {
            Path('src'): Volume({
                Path('section1'): Page('# Section 1\n## Paragraph 1'),
                Path('section1/page1.md'): Page('# Page 1.1\n## Paragraph 1'),  # <- current page
                Path('section1/page2.md'): Page('# Page 1.2\n## Paragraph 1'),
                Path('section2'): Page('# Section 2\n## Paragraph 1'),
                Path('section2/page1.md'): Page('# Page 2.1\n## Paragraph 1'),
                Path('section2/page2.md'): Page('# Page 2.2\n## Paragraph 1'),
            })
        })
        self.volume = self.project.get_volume()
        self.processor = FakeProcessor()
        for page in self.volume.pages:
            await self.processor.process1(page)

        self.current_page = self.volume.pages_by_path[Path('section1/page1.md')]

    def test_combined_toc(self):
        self.maxDiff = None

        data = {
            CombinedToc.NEVER:
                Toc((
                    TocItem('Section 1', '.', is_selected=True, children=Toc((
                        TocItem('Page 1.1', '', is_current=True, is_selected=True),
                        TocItem('Page 1.2', 'page2.md'),
                    ))),
                    TocItem('Section 2', '../section2', children=Toc((
                        TocItem('Page 2.1', '../section2/page1.md'),
                        TocItem('Page 2.2', '../section2/page2.md'),
                    ))),
                )),

            CombinedToc.CURRENT:
                Toc((
                    TocItem('Section 1', '.', is_selected=True, children=Toc((
                        TocItem('Page 1.1', '', is_current=True, is_selected=True, children=Toc((
                            TocItem('Paragraph 1', '#paragraph-1'),
                        ))),
                        TocItem('Page 1.2', 'page2.md'),
                    ))),
                    TocItem('Section 2', '../section2', children=Toc((
                        TocItem('Page 2.1', '../section2/page1.md'),
                        TocItem('Page 2.2', '../section2/page2.md'),
                    ))),
                )),

            CombinedToc.ALWAYS:
                Toc((
                    TocItem('Section 1', '.', is_selected=True, children=Toc((
                        TocItem('Paragraph 1', '.#paragraph-1'),
                        TocItem('Page 1.1', '', is_current=True, is_selected=True, children=Toc((
                            TocItem('Paragraph 1', '#paragraph-1'),
                        ))),
                        TocItem('Page 1.2', 'page2.md', children=Toc((
                            TocItem('Paragraph 1', 'page2.md#paragraph-1'),
                        ))),
                    ))),
                    TocItem('Section 2', '../section2', children=Toc((
                        TocItem('Paragraph 1', '../section2#paragraph-1'),
                        TocItem('Page 2.1', '../section2/page1.md', children=Toc((
                            TocItem('Paragraph 1', '../section2/page1.md#paragraph-1'),
                        ))),
                        TocItem('Page 2.2', '../section2/page2.md', children=Toc((
                            TocItem('Paragraph 1', '../section2/page2.md#paragraph-1'),
                        ))),
                    ))),
                )),
        }

        for setting in CombinedToc:
            with self.subTest(setting.name):
                expected = data[setting]
                actual = toc(self.volume,
                             processor=self.processor,
                             current_page=self.current_page,
                             combined_toc=setting)
                self.assertEqual(str(expected), str(actual))


class FakeProcessor(Processor):
    def make_internal_url(self, href: PageHref, *, page: Page) -> str:
        if page is href.target:
            return ''
        return relpath(href.target.path_in_volume, start=page.path_in_volume.parent)


if __name__ == '__main__':
    main()
