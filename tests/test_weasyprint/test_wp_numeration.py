from unittest import main
from unittest.mock import Mock

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from sobiraka.models import FileSystem, Page, Project, Volume
from sobiraka.models.config import Config, Config_Content, Config_PDF
from sobiraka.utils import RelativePath


class TestWeasyPrint_Numeration(WeasyPrintProjectTestCase):
    PAGE_LIMIT = 4

    def _init_project(self) -> Project:
        fs = Mock(FileSystem)
        config = Config(content=Config_Content(numeration=True))
        return Project(fs, {
            RelativePath(): Volume(config, {
                RelativePath(): Page('Here is some introduction.'),

                RelativePath('chapter1'): Page('# Chapter 1\n\n@toc'),
                RelativePath('chapter1/section1'): Page('# Section 1\n\n@toc'),
                RelativePath('chapter1/section1/page1.md'): Page('# Page 1'),
                RelativePath('chapter1/section1/page2.md'): Page('# Page 2'),
                RelativePath('chapter1/section2'): Page('# Section 2'),
                RelativePath('chapter1/section2/page1.md'): Page('# Page 1'),
                RelativePath('chapter1/section2/page2.md'): Page('# Page 2'),
                RelativePath('chapter1/section3'): Page('# Section 3'),
                RelativePath('chapter1/section3/page1.md'): Page('# Page 1'),
                RelativePath('chapter1/section3/page2.md'): Page('# Page 2'),

                RelativePath('chapter2'): Page('# Chapter 2'),
                RelativePath('chapter2/section1'): Page('# Section 1'),
                RelativePath('chapter2/section1/page1.md'): Page('# Page 1'),
                RelativePath('chapter2/section1/page2.md'): Page('# Page 2'),
                RelativePath('chapter2/section2'): Page('# Section 2'),
                RelativePath('chapter2/section2/page1.md'): Page('# Page 1'),
                RelativePath('chapter2/section2/page2.md'): Page('# Page 2'),
                RelativePath('chapter2/section3'): Page('# Section 3'),
                RelativePath('chapter2/section3/page1.md'): Page('# Page 1'),
                RelativePath('chapter2/section3/page2.md'): Page('# Page 2'),

                RelativePath('chapter3'): Page('# Chapter 3'),
                RelativePath('chapter3/section1'): Page('# Section 1'),
                RelativePath('chapter3/section1/page1.md'): Page('# Page 1'),
                RelativePath('chapter3/section1/page2.md'): Page('# Page 2'),
                RelativePath('chapter3/section2'): Page('# Section 2'),
                RelativePath('chapter3/section2/page1.md'): Page('# Page 1'),
                RelativePath('chapter3/section2/page2.md'): Page('# Page 2'),
                RelativePath('chapter3/section3'): Page('# Section 3'),
                RelativePath('chapter3/section3/page1.md'): Page('# Page 1'),
                RelativePath('chapter3/section3/page2.md'): Page('# Page 2'),
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
            content=Config_Content(numeration=True),
            pdf=Config_PDF(combined_toc=True),
        )


del SinglePageProjectTest, WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
