from math import inf
from unittest import main

from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeBuilder
from helpers.fakeproject import FakeDocument, FakeProject
from sobiraka.models import Project, Status
from sobiraka.models.config import CombinedToc, Config, Config_Content, Config_Paths
from sobiraka.processing.toc import Toc, TocItem, toc
from sobiraka.utils import RelativePath, TocNumber, Unnumbered


# Test that:
# - `config.content.numeration` affects whether `toc()` adds numbers to items,
# - numeration works correctly in a combined TOC with multiple levels of anchors,
# - `{-}` skips numeration for the given item and its children.


class TestNumerate(ProjectTestCase[FakeBuilder]):
    REQUIRE = Status.PROCESS3
    numeration_enabled = True

    def _init_project(self) -> Project:
        config = Config(
            paths=Config_Paths(root=RelativePath('src')),
            content=Config_Content(numeration=self.numeration_enabled),
        )
        return FakeProject({
            'src': FakeDocument(config, {
                'index.md': '',
                '1-preface.md': '# preface {-}',
                '2-intro.md': '',

                # Numeration disabled for one chapter
                '3-installation': {
                    'index.md': '# installation {-}',
                    'linux.md': '',
                    'macos.md': '',
                    'windows.md': '',
                },

                # Numeration enabled again
                '4-usage': {
                    'index.md': '',
                    'cli.md': '',
                    'ui.md': '',
                },

                # Numeration of chapters and subpages together
                '5-troubleshooting': {
                    'index.md': '''
                        ## cannot start
                        ## cannot work
                        ## cannot explain {-}
                        ### no number here
                        #### or here
                        ### or even here
                        ## cannot stop
                    ''',
                    'advanced.md': '''
                        ## cannot believe how smart i am {-}
                        ## cannot trust this documentation
                        ## cannot possibly need this
                    ''',
                },

                '6-outro.md': '',
                '7-credits.md': '# credits {-}',
            })
        })

    async def test_numeration(self):
        expected = expected_data(self.numeration_enabled)

        actual = toc(self.project.get_document().root_page,
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
        return Unnumbered()

    return Toc(
        TocItem('preface', 'preface.md'),
        TocItem('intro', 'intro.md', number=num(1)),
        TocItem('installation', 'installation/', children=Toc(
            TocItem('linux', 'installation/linux.md'),
            TocItem('macos', 'installation/macos.md'),
            TocItem('windows', 'installation/windows.md'),
        )),
        TocItem('usage', 'usage/', number=num(2), children=Toc(
            TocItem('cli', 'usage/cli.md', number=num(2, 1)),
            TocItem('ui', 'usage/ui.md', number=num(2, 2)),
        )),
        TocItem('troubleshooting', 'troubleshooting/', number=num(3), children=Toc(
            TocItem('cannot start', 'troubleshooting/#cannot-start', number=num(3, 1)),
            TocItem('cannot work', 'troubleshooting/#cannot-work', number=num(3, 2)),
            TocItem('cannot explain', 'troubleshooting/#cannot-explain', children=Toc(
                TocItem('no number here', 'troubleshooting/#no-number-here', children=Toc(
                    TocItem('or here', 'troubleshooting/#or-here'),
                )),
                TocItem('or even here', 'troubleshooting/#or-even-here'),
            )),
            TocItem('cannot stop', 'troubleshooting/#cannot-stop', number=num(3, 3)),
            TocItem('advanced', 'troubleshooting/advanced.md', number=num(3, 4), children=Toc(
                TocItem('cannot believe how smart i am',
                        'troubleshooting/advanced.md#cannot-believe-how-smart-i-am'),
                TocItem('cannot trust this documentation',
                        'troubleshooting/advanced.md#cannot-trust-this-documentation', number=num(3, 4, 1)),
                TocItem('cannot possibly need this',
                        'troubleshooting/advanced.md#cannot-possibly-need-this', number=num(3, 4, 2)),
            )),
        )),
        TocItem('outro', 'outro.md', number=num(4)),
        TocItem('credits', 'credits.md'),
    )


del ProjectTestCase

if __name__ == '__main__':
    main()
