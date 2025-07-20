from unittest import main

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from helpers.fakeproject import FakeDocument, FakeProject
from sobiraka.models import Project
from sobiraka.models.config import Config, Config_Content, Config_PDF, Config_Paths
from sobiraka.utils import RelativePath


class TestWeasyPrint_Numeration(WeasyPrintProjectTestCase):
    PAGE_LIMIT = 4

    def _init_project(self) -> Project:
        config = Config(
            paths=Config_Paths(root=RelativePath('src')),
            content=Config_Content(numeration=True),
            variables=dict(NOCOVER=True),
        )

        return FakeProject({
            'src': FakeDocument(config, {
                'index.md': 'Here is some introduction.',

                'chapter1/index.md': '# Chapter 1\n\n@toc',
                'chapter1/section1/index.md': '# Section 1\n\n@toc',
                'chapter1/section1/page1.md': '# Page 1',
                'chapter1/section1/page2.md': '# Page 2',
                'chapter1/section2/index.md': '# Section 2',
                'chapter1/section2/page1.md': '# Page 1',
                'chapter1/section2/page2.md': '# Page 2',
                'chapter1/section3/index.md': '# Section 3',
                'chapter1/section3/page1.md': '# Page 1',
                'chapter1/section3/page2.md': '# Page 2',

                'chapter2/index.md': '# Chapter 2',
                'chapter2/section1/index.md': '# Section 1',
                'chapter2/section1/page1.md': '# Page 1',
                'chapter2/section1/page2.md': '# Page 2',
                'chapter2/section2/index.md': '# Section 2',
                'chapter2/section2/page1.md': '# Page 1',
                'chapter2/section2/page2.md': '# Page 2',
                'chapter2/section3/index.md': '# Section 3',
                'chapter2/section3/page1.md': '# Page 1',
                'chapter2/section3/page2.md': '# Page 2',

                'chapter3/index.md': '# Chapter 3',
                'chapter3/section1/index.md': '# Section 1',
                'chapter3/section1/page1.md': '# Page 1',
                'chapter3/section1/page2.md': '# Page 2',
                'chapter3/section2/index.md': '# Section 2',
                'chapter3/section2/page1.md': '# Page 1',
                'chapter3/section2/page2.md': '# Page 2',
                'chapter3/section3/index.md': '# Section 3',
                'chapter3/section3/page1.md': '# Page 1',
                'chapter3/section3/page2.md': '# Page 2',
            }),
        })


class TestWeasyPrint_Numeration_SinglePage(SinglePageProjectTest, WeasyPrintProjectTestCase):
    SOURCE = '''
        # Ahaha
        ## Section 1
        ## Section 2
    '''

    PAGE_LIMIT = 1

    def _init_config(self) -> Config:
        return Config(
            paths=Config_Paths(root=RelativePath('src')),
            content=Config_Content(numeration=True),
            pdf=Config_PDF(combined_toc=True),
            variables=dict(NOCOVER=True),
        )


del SinglePageProjectTest, WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
