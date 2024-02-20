from math import inf
from pathlib import Path
from textwrap import dedent
from unittest import main

from abstracttests.abstracttestwithrt import AbstractTestWithRtPages
from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakefilesystem import FakeFileSystem
from helpers.fakeprocessor import FakeProcessor
from sobiraka.models import Page, Project, Volume
from sobiraka.models.config import CombinedToc, Config, Config_Content
from sobiraka.processing.toc import Toc, TocItem, toc
from sobiraka.utils import TocNumber, Unnumbered

"""
Test that:
- `config.content.numeration` affects whether `toc()` adds numbers to items,
- numeration works correctly in a combined TOC with multiple levels of anchors,
- `{-}` skips numeration for the given item and its children.
"""


class TestNumerate(ProjectTestCase[FakeProcessor], AbstractTestWithRtPages):
    numeration_enabled = True

    def _init_project(self) -> Project:
        config = Config(
            content=Config_Content(numeration=self.numeration_enabled),
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
        expected = expected_data(self.numeration_enabled)

        await self.processor.process3(self.project.get_volume())
        actual = toc(self.project.get_volume(),
                     processor=self.processor,
                     toc_depth=inf,
                     combined_toc=CombinedToc.ALWAYS)

        self.assertEqual(expected, actual)


class TestDontNumerate(TestNumerate):
    numeration_enabled = False


def expected_data(numeration_enabled: bool) -> Toc:
    def num(*numbers: int) -> TocNumber:
        if numeration_enabled:
            return TocNumber(*numbers)
        else:
            return Unnumbered()

    return Toc(
        TocItem('preface', '1-preface.md'),
        TocItem('intro', '2-intro.md', number=num(1)),
        TocItem('installation', '3-installation', children=Toc(
            TocItem('linux', '3-installation/linux.md'),
            TocItem('macos', '3-installation/macos.md'),
            TocItem('windows', '3-installation/windows.md'),
        )),
        TocItem('usage', '4-usage', number=num(2), children=Toc(
            TocItem('cli', '4-usage/cli.md', number=num(2, 1)),
            TocItem('ui', '4-usage/ui.md', number=num(2, 2)),
        )),
        TocItem('troubleshooting', '5-troubleshooting', number=num(3), children=Toc(
            TocItem('cannot start', '5-troubleshooting#cannot-start', number=num(3, 1)),
            TocItem('cannot work', '5-troubleshooting#cannot-work', number=num(3, 2)),
            TocItem('cannot explain', '5-troubleshooting#cannot-explain', children=Toc(
                TocItem('no number here', '5-troubleshooting#no-number-here', children=Toc(
                    TocItem('or here', '5-troubleshooting#or-here'),
                )),
                TocItem('or even here', '5-troubleshooting#or-even-here'),
            )),
            TocItem('cannot stop', '5-troubleshooting#cannot-stop', number=num(3, 3)),
            TocItem('advanced', '5-troubleshooting/advanced.md', number=num(3, 4), children=Toc(
                TocItem('cannot believe how smart i am',
                        '5-troubleshooting/advanced.md#cannot-believe-how-smart-i-am'),
                TocItem('cannot trust this documentation',
                        '5-troubleshooting/advanced.md#cannot-trust-this-documentation', number=num(3, 4, 1)),
                TocItem('cannot possibly need this',
                        '5-troubleshooting/advanced.md#cannot-possibly-need-this', number=num(3, 4, 2)),
            )),
        )),
        TocItem('outro', '6-outro.md', number=num(4)),
        TocItem('credits', '7-credits.md'),
    )


del ProjectTestCase

if __name__ == '__main__':
    main()
