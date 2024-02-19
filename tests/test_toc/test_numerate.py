from pathlib import Path
from textwrap import dedent
from unittest import main

from abstracttests.abstracttestwithrt import AbstractTestWithRtPages
from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakefilesystem import FakeFileSystem
from helpers.fakeprocessor import FakeProcessor
from sobiraka.models import Page, Project, Volume
from sobiraka.models.config import CombinedToc, Config, Config_Content, Config_HTML
from sobiraka.processing.toc import Toc, TocItem, toc
from sobiraka.utils import TocNumber


class TestNumeration(ProjectTestCase[FakeProcessor], AbstractTestWithRtPages):

    def _init_project(self) -> Project:
        config = Config(
            content=Config_Content(numeration=True),
            html=Config_HTML(combined_toc=CombinedToc.ALWAYS),
        )
        return Project(FakeFileSystem(), {
            Path('src'): Volume(config, {
                Path(): Page(),
                Path() / '1-preface.md': Page('# preface {-}'),
                Path() / '2-intro.md': Page(),

                # Numeration disabled for one chapter
                Path() / '3-installation': Page('# installation {-}'),
                Path() / '3-installation' / 'linux.md': Page(),
                Path() / '3-installation' / 'macos.md': Page(),
                Path() / '3-installation' / 'windows.md': Page(),

                # Numeration enabled again
                Path() / '4-usage': Page(),
                Path() / '4-usage' / 'cli.md': Page(),
                Path() / '4-usage' / 'ui.md': Page(),

                # Numeration of chapters and subpages together
                Path() / '5-troubleshooting': Page(dedent('''
                    ## cannot start
                    ## cannot work
                    ## cannot explain {-}
                    ### no number here
                    #### or here
                    ### or even here
                    ## cannot stop
                ''')),
                Path() / '5-troubleshooting' / 'advanced.md': Page(dedent('''
                    ## cannot believe how smart i am {-}
                    ## cannot trust this documentation
                    ## cannot possibly need this
                ''')),

                Path() / '6-outro.md': Page(),
                Path() / '7-credits.md': Page('# credits {-}'),
            })
        })

    def _init_processor(self) -> FakeProcessor:
        return FakeProcessor()

    async def test_numeration(self):
        expected = Toc(
            TocItem('preface', '1-preface.md'),
            TocItem('intro', '2-intro.md', number=TocNumber(1)),
            TocItem('installation', '3-installation', children=Toc(
                TocItem('linux', '3-installation/linux.md'),
                TocItem('macos', '3-installation/macos.md'),
                TocItem('windows', '3-installation/windows.md'),
            )),
            TocItem('usage', '4-usage', number=TocNumber(2), children=Toc(
                TocItem('cli', '4-usage/cli.md', number=TocNumber(2, 1)),
                TocItem('ui', '4-usage/ui.md', number=TocNumber(2, 2)),
            )),
            TocItem('troubleshooting', '5-troubleshooting', number=TocNumber(3), children=Toc(
                TocItem('cannot start', '5-troubleshooting#cannot-start', number=TocNumber(3, 1)),
                TocItem('cannot work', '5-troubleshooting#cannot-work', number=TocNumber(3, 2)),
                TocItem('cannot explain', '5-troubleshooting#cannot-explain', children=Toc(
                    TocItem('no number here', '5-troubleshooting#no-number-here', children=Toc(
                        TocItem('or here', '5-troubleshooting#or-here'),
                    )),
                    TocItem('or even here', '5-troubleshooting#or-even-here'),
                )),
                TocItem('cannot stop', '5-troubleshooting#cannot-stop', number=TocNumber(3, 3)),
                TocItem('advanced', '5-troubleshooting/advanced.md', number=TocNumber(3, 4), children=Toc(
                    TocItem('cannot believe how smart i am',
                            '5-troubleshooting/advanced.md#cannot-believe-how-smart-i-am'),
                    TocItem('cannot trust this documentation',
                            '5-troubleshooting/advanced.md#cannot-trust-this-documentation', number=TocNumber(3, 4, 1)),
                    TocItem('cannot possibly need this',
                            '5-troubleshooting/advanced.md#cannot-possibly-need-this', number=TocNumber(3, 4, 2)),
                )),
            )),
            TocItem('outro', '6-outro.md', number=TocNumber(4)),
            TocItem('credits', '7-credits.md'),
        )

        await self.processor.process3(self.project.get_volume())
        actual = toc(self.project.get_volume(), processor=self.processor)
        self.assertEqual(expected, actual)


del ProjectTestCase

if __name__ == '__main__':
    main()
