from typing import Literal
from unittest import main

from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project
from sobiraka.models.config import Config, Config_Content, Config_PDF, Config_Paths
from sobiraka.utils import RelativePath


class TestWeasyPrint_Headers_Abstract(WeasyPrintProjectTestCase):
    POLICY: Literal['local', 'global']
    NUMERATION: bool = False

    def _init_project(self) -> Project:
        config = Config(
            paths=Config_Paths(
                root=RelativePath('src'),
            ),
            content=Config_Content(
                numeration=self.NUMERATION,
            ),
            pdf=Config_PDF(
                custom_styles=(RelativePath('style.css'),),
                headers_policy=self.POLICY,
            ),
            variables=dict(NOCOVER=True),
        )

        project = FakeProject({
            'src': FakeVolume(config, {
                'index.md': '# Intro\n## Section 1\n## Section 2',
                'p1/index.md': '# Part 1',
                'p1/s1/index.md': '# Section 1\n## Paragraph 1.1',
                'p1/s2/index.md': '# Section 2\n## Paragraph 2.1',
            }),
        })

        project.fs.add_files({
            'style.css': '''
                /* Skip the TOC, for the sake of compactness. */
                div.toc { display: none; }
                
                /* Use horizontal lines but skip the page breaks, for the sake of compactness. */
                h1, h2, h3, h4, h5, h6 {
                    page: auto !important;
                    page-break-before: auto !important;
                }
                [data-local-level='1'] {
                    border-top: 1px solid skyblue;
                    margin-top: 1rem !important;
                    padding-top: 1rem;
                }
                
                /* Show the rendered header level next to it. */
                h1::after, h2::after, h3::after, h4::after, h5::after, h6::after {
                    color: darkorange;
                    font-size: 14pt;
                }
                h1::after { content: ' ← H1'; }
                h2::after { content: ' ← H2'; }
                h3::after { content: ' ← H3'; }
                h4::after { content: ' ← H4'; }
                h5::after { content: ' ← H5'; }
                h6::after { content: ' ← H6'; }
            '''
        })

        return project


class TestWeasyPrint_Headers_Global(TestWeasyPrint_Headers_Abstract):
    POLICY = 'global'


class TestWeasyPrint_Headers_Global_Numerated(TestWeasyPrint_Headers_Abstract):
    POLICY = 'global'
    NUMERATION = True


class TestWeasyPrint_Headers_Local(TestWeasyPrint_Headers_Abstract):
    POLICY = 'local'


class TestWeasyPrint_Headers_Local_Numerated(TestWeasyPrint_Headers_Abstract):
    POLICY = 'local'
    NUMERATION = True


del WeasyPrintProjectTestCase, TestWeasyPrint_Headers_Abstract

if __name__ == '__main__':
    main()
