from math import inf
from textwrap import dedent
from unittest import main

from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeBuilder, FakeFileSystem
from sobiraka.models import Page, PageStatus, Project, Volume
from sobiraka.models.config import CombinedToc, Config, Config_Content
from sobiraka.processing.toc import Toc, TocItem, toc
from sobiraka.utils import RelativePath, TocNumber, Unnumbered

"""
Test that:
- `config.content.numeration` affects whether `toc()` adds numbers to items,
- numeration works correctly in a combined TOC with multiple levels of anchors,
- `{-}` skips numeration for the given item and its children.
"""


class TestNumerate(ProjectTestCase[FakeBuilder]):
    REQUIRE = PageStatus.PROCESS3
    numeration_enabled = True

    def _init_project(self) -> Project:
        config = Config(
            content=Config_Content(numeration=self.numeration_enabled),
        )
        return Project(FakeFileSystem(), {
            RelativePath('src'): Volume(config, {
                RelativePath(): Page(),
                RelativePath() / '1-preface.md': Page('# preface {-}'),
                RelativePath() / '2-intro.md': Page(),

                # Numeration disabled for one chapter
                RelativePath() / '3-installation': Page('# installation {-}'),
                RelativePath() / '3-installation' / 'linux.md': Page(),
                RelativePath() / '3-installation' / 'macos.md': Page(),
                RelativePath() / '3-installation' / 'windows.md': Page(),

                # Numeration enabled again
                RelativePath() / '4-usage': Page(),
                RelativePath() / '4-usage' / 'cli.md': Page(),
                RelativePath() / '4-usage' / 'ui.md': Page(),

                # Numeration of chapters and subpages together
                RelativePath() / '5-troubleshooting': Page(dedent('''
                    ## cannot start
                    ## cannot work
                    ## cannot explain {-}
                    ### no number here
                    #### or here
                    ### or even here
                    ## cannot stop
                ''')),
                RelativePath() / '5-troubleshooting' / 'advanced.md': Page(dedent('''
                    ## cannot believe how smart i am {-}
                    ## cannot trust this documentation
                    ## cannot possibly need this
                ''')),

                RelativePath() / '6-outro.md': Page(),
                RelativePath() / '7-credits.md': Page('# credits {-}'),
            })
        })

    async def test_numeration(self):
        expected = expected_data(self.numeration_enabled)

        actual = toc(self.project.get_volume().root_page,
                     builder=self.builder,
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
