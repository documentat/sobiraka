from abc import ABCMeta
from unittest import main

from abstracttests.projecttestcase import FailingProjectTestCase
from sobiraka.processing.web import Head, HeadCssFile, HeadCssUrl, HeadJsFile, HeadJsUrl
from sobiraka.utils import RelativePath
from test_processing.test_highlight.abstract import AbstractHighlightTest


class AbstractHighlightTest_Prism(AbstractHighlightTest, metaclass=ABCMeta):
    EXPECTED_RENDER = '<pre><code class="language-shell">echo 1</code></pre>'


class TestPrism_cdnjs(AbstractHighlightTest_Prism):
    CONFIG = {'prism': {
        'version': '1.28.0',
        'location': 'cdnjs',
        'style': 'tomorrow',
    }}
    EXPECTED_HEAD = Head((
        HeadJsUrl('https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-core.min.js'),
        HeadJsUrl('https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/plugins/autoloader/prism-autoloader.min.js'),
        HeadCssUrl('https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/themes/prism-tomorrow.min.css'),
    ))


class TestPrism_jsdelivr(AbstractHighlightTest_Prism):
    CONFIG = {'prism': {
        'version': '1.28.0',
        'location': 'jsdelivr',
        'style': 'tomorrow',
    }}
    EXPECTED_HEAD = Head((
        HeadJsUrl('https://cdn.jsdelivr.net/npm/prismjs@1.28.0/components/prism-core.min.js'),
        HeadJsUrl('https://cdn.jsdelivr.net/npm/prismjs@1.28.0/plugins/autoloader/prism-autoloader.min.js'),
        HeadCssUrl('https://cdn.jsdelivr.net/npm/prismjs@1.28.0/themes/prism-tomorrow.min.css'),
    ))


class TestPrism_unpkg(AbstractHighlightTest_Prism):
    CONFIG = {'prism': {
        'version': '1.28.0',
        'location': 'unpkg',
        'style': 'tomorrow',
    }}
    EXPECTED_HEAD = Head((
        HeadJsUrl('https://unpkg.com/prismjs@1.28.0/components/prism-core.min.js'),
        HeadJsUrl('https://unpkg.com/prismjs@1.28.0/plugins/autoloader/prism-autoloader.min.js'),
        HeadCssUrl('https://unpkg.com/prismjs@1.28.0/themes/prism-tomorrow.min.css'),
    ))


class TestPrism_URL(AbstractHighlightTest_Prism):
    CONFIG = {'prism': {
        'version': '1.28.0',
        'location': 'https://example.com/hljs',
        'style': 'tomorrow',
    }}
    EXPECTED_HEAD = Head((
        HeadJsUrl('https://example.com/hljs/components/prism-core.min.js'),
        HeadJsUrl('https://example.com/hljs/plugins/autoloader/prism-autoloader.min.js'),
        HeadCssUrl('https://example.com/hljs/themes/prism-tomorrow.min.css'),
    ))


class TestPrism_Local(AbstractHighlightTest_Prism):
    CONFIG = {'prism': {
        'location': './libs/prism',
        'style': 'tomorrow',
    }}
    FILES = (
        'libs/prism/components/prism-core.min.js',
        'libs/prism/plugins/autoloader/prism-autoloader.min.js',
        'libs/prism/themes/prism-tomorrow.min.css',
    )
    EXPECTED_HEAD = Head((
        HeadJsFile(RelativePath('libs/prism/components/prism-core.min.js')),
        HeadJsFile(RelativePath('libs/prism/plugins/autoloader/prism-autoloader.min.js')),
        HeadCssFile(RelativePath('libs/prism/themes/prism-tomorrow.min.css')),
    ))


class TestPrism_Local_MissingCSS(AbstractHighlightTest_Prism, FailingProjectTestCase):
    CONFIG = {'prism': {
        'location': './libs/prism',
        'style': 'tomorrow',
    }}
    FILES = (
        'libs/prism/components/prism-core.min.js',
        'libs/prism/plugins/autoloader/prism-autoloader.min.js',
    )
    EXPECTED_EXCEPTION_TYPES = {FileNotFoundError}
    test_head = None
    test_render = None


class TestPrism_Local_MissingJS(AbstractHighlightTest_Prism, FailingProjectTestCase):
    CONFIG = {'prism': {
        'location': './libs/prism',
        'style': 'tomorrow',
    }}
    FILES = (
        'libs/prism/plugins/autoloader/prism-autoloader.min.js',
        'libs/prism/themes/prism-tomorrow.min.css',
    )
    EXPECTED_EXCEPTION_TYPES = {FileNotFoundError}
    test_head = None
    test_render = None


class TestPrism_Local_MissingJS_Autoloader(AbstractHighlightTest_Prism, FailingProjectTestCase):
    CONFIG = {'prism': {
        'location': './libs/prism',
        'style': 'tomorrow',
    }}
    FILES = (
        'libs/prism/components/prism-core.min.js',
        'libs/prism/themes/prism-tomorrow.min.css',
    )
    EXPECTED_EXCEPTION_TYPES = {FileNotFoundError}
    test_head = None
    test_render = None


del AbstractHighlightTest, AbstractHighlightTest_Prism, FailingProjectTestCase



if __name__ == '__main__':
    main()