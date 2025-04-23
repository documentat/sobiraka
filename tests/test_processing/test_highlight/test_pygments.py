from abc import ABCMeta
from textwrap import dedent
from unittest import main

from abstracttests.weasyprintprojecttestcase import WeasyPrintProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project
from sobiraka.models.config import Config, Config_PDF, Config_Paths, Config_Pygments
from sobiraka.processing.web import Head, HeadCssFile
from sobiraka.utils import RelativePath
from .abstract import AbstractHighlightTest


class AbstractHighlightTest_Pygments(AbstractHighlightTest, metaclass=ABCMeta):
    EXPECTED_RENDER = '<pre><code class="pygments"><span class="nb">echo</span><span class="w">' \
                      ' </span><span class="m">1</span></code></pre>'


class TestPygments(AbstractHighlightTest_Pygments):
    CONFIG = 'pygments'
    EXPECTED_HEAD = Head((
        HeadCssFile(RelativePath('_static/css/pygments-default.css')),
    ))


class TestPygments_NoStyle(AbstractHighlightTest_Pygments):
    CONFIG = {'pygments': {
        'style': None,
    }}
    EXPECTED_HEAD = Head()


class TestPygments_CustomClasses(AbstractHighlightTest_Pygments):
    CONFIG = {'pygments': {
        'style': 'xcode',
        'pre_class': 'mypre',
        'code_class': 'mycode',
    }}
    EXPECTED_HEAD = Head((
        HeadCssFile(RelativePath('_static/css/pygments-xcode.css')),
    ))
    EXPECTED_RENDER = '<pre class="mypre"><code class="mycode"><span class="nb">echo</span><span class="w">' \
                      ' </span><span class="m">1</span></code></pre>'


class TestPygments_WeasyPrint_PHP(WeasyPrintProjectTestCase):
    CONTENT = dedent('''
        # PHP highlighting examples
        
        Not highlighted:
        ```php
        echo 'Hello, world!'
        ```
        
        Highlighted because of the opening tag:
        ```php
        <? echo 'Hello, world!'
        ```
        
        Highlighted because of the option:
        ```php {startinline=true}
        echo 'Hello, world!'
        ```
    ''')

    def _init_project(self) -> Project:
        config = Config(
            paths=Config_Paths(root=RelativePath('src')),
            pdf=Config_PDF(highlight=Config_Pygments(style='vs'))
        )
        return FakeProject({
            'src': FakeVolume(config, {
                'index.md': self.CONTENT,
            })
        })


del AbstractHighlightTest, AbstractHighlightTest_Pygments, WeasyPrintProjectTestCase

if __name__ == '__main__':
    main()
