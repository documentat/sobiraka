from unittest import main
from unittest.mock import Mock

from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from sobiraka.models import FileSystem, Page, Project, Volume
from sobiraka.models.config import Config, Config_Content
from sobiraka.utils import RelativePath


class TestWeasyPrint_Numeration(WeasyPrintProjectTestCase):
    PAGE_LIMIT = 1

    def _init_project(self) -> Project:
        fs = Mock(FileSystem)
        config = Config(content=Config_Content(numeration=True))
        return Project(fs, {
            RelativePath(): Volume(config, {
                RelativePath('chapter1'): Page('# Chapter 1'),
                RelativePath('chapter1/section1'): Page('# Section 1'),
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


del WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
