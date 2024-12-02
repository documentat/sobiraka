from abc import ABCMeta
from unittest import main

from sobiraka.models.config import Config_Pygments
from sobiraka.processing.web import Head, HeadCssFile
from sobiraka.utils import RelativePath
from test_processing.test_highlight.abstract import AbstractHighlightTest


class AbstractHighlightTest_Pygments(AbstractHighlightTest, metaclass=ABCMeta):
    EXPECTED_RENDER = '<pre><code class="pygments"><span class="nb">echo</span><span class="w"> </span><span class="m">1</span></code></pre>'


class TestPygments(AbstractHighlightTest_Pygments):
    CONFIG = Config_Pygments(
        style='xcode',
    )
    EXPECTED_HEAD = Head((
        HeadCssFile(RelativePath('_static/css/pygments-xcode.css')),
    ))


class TestPygments_CustomClasses(AbstractHighlightTest_Pygments):
    CONFIG = Config_Pygments(
        style='xcode',
        pre_class='mypre',
        code_class='mycode',
    )
    EXPECTED_HEAD = Head((
        HeadCssFile(RelativePath('_static/css/pygments-xcode.css')),
    ))
    EXPECTED_RENDER = '<pre class="mypre"><code class="mycode"><span class="nb">echo</span><span class="w"> </span><span class="m">1</span></code></pre>'


del AbstractHighlightTest, AbstractHighlightTest_Pygments

if __name__ == '__main__':
    main()
