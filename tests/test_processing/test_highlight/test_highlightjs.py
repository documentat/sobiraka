from abc import ABCMeta
from unittest import main

from abstracttests.projecttestcase import FailingProjectTestCase
from sobiraka.processing.web import Head, HeadCssFile, HeadCssUrl, HeadJsFile, HeadJsUrl
from sobiraka.utils import RelativePath
from test_processing.test_highlight.abstract import AbstractHighlightTest


class AbstractHighlightTest_HighlightJS(AbstractHighlightTest, metaclass=ABCMeta):
    EXPECTED_RENDER = '<pre><code class="language-shell">echo 1</code></pre>'


class TestHighlightJS_cdnjs(AbstractHighlightTest_HighlightJS):
    CONFIG = {'highlightjs': {
        'version': '10.0.0',
        'location': 'cdnjs',
        'style': 'github',
    }}
    EXPECTED_HEAD = Head((
        HeadJsUrl('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.0.0/highlight.min.js'),
        HeadCssUrl('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.0.0/styles/github.min.css'),
        HeadJsFile(RelativePath('_static/js/init-highlight.js')),
    ))


class TestHighlightJS_jsdelivr(AbstractHighlightTest_HighlightJS):
    CONFIG = {'highlightjs': {
        'version': '10.0.0',
        'location': 'jsdelivr',
        'style': 'github',
    }}
    EXPECTED_HEAD = Head((
        HeadJsUrl('https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@10.0.0/highlight.min.js'),
        HeadCssUrl('https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@10.0.0/styles/github.min.css'),
        HeadJsFile(RelativePath('_static/js/init-highlight.js')),
    ))


class TestHighlightJS_unpkg(AbstractHighlightTest_HighlightJS):
    CONFIG = {'highlightjs': {
        'version': '10.0.0',
        'location': 'unpkg',
        'style': 'github',
    }}
    EXPECTED_HEAD = Head((
        HeadJsUrl('https://unpkg.com/@highlightjs/cdn-assets@10.0.0/highlight.min.js'),
        HeadCssUrl('https://unpkg.com/@highlightjs/cdn-assets@10.0.0/styles/github.min.css'),
        HeadJsFile(RelativePath('_static/js/init-highlight.js')),
    ))


class TestHighlightJS_URL(AbstractHighlightTest_HighlightJS):
    CONFIG = {'highlightjs': {
        'version': '10.0.0',
        'location': 'https://example.com/hljs',
        'style': 'github',
    }}
    EXPECTED_HEAD = Head((
        HeadJsUrl('https://example.com/hljs/highlight.min.js'),
        HeadCssUrl('https://example.com/hljs/styles/github.min.css'),
        HeadJsFile(RelativePath('_static/js/init-highlight.js')),
    ))


class TestHighlightJS_Local(AbstractHighlightTest_HighlightJS):
    CONFIG = {'highlightjs': {
        'location': './libs/hljs',
        'style': 'github',
    }}
    FILES = (
        'libs/hljs/highlight.min.js',
        'libs/hljs/styles/github.min.css',
    )
    EXPECTED_HEAD = Head((
        HeadJsFile(RelativePath('libs/hljs/highlight.min.js')),
        HeadCssFile(RelativePath('libs/hljs/styles/github.min.css')),
        HeadJsFile(RelativePath('_static/js/init-highlight.js')),
    ))


class TestHighlightJS_Local_MissingCSS(AbstractHighlightTest_HighlightJS, FailingProjectTestCase):
    CONFIG = {'highlightjs': {
        'location': './libs/hljs',
        'style': 'github',
    }}
    FILES = (
        'libs/hljs/highlight.min.js',
    )
    EXPECTED_EXCEPTION_TYPES = {FileNotFoundError}
    test_head = None
    test_render = None


class TestHighlightJS_Local_MissingJS(AbstractHighlightTest_HighlightJS, FailingProjectTestCase):
    CONFIG = {'highlightjs': {
        'location': './libs/hljs',
        'style': 'github',
    }}
    FILES = (
        'libs/hljs/styles/github.min.css',
    )
    EXPECTED_EXCEPTION_TYPES = {FileNotFoundError}
    test_head = None
    test_render = None


del AbstractHighlightTest, AbstractHighlightTest_HighlightJS, FailingProjectTestCase

if __name__ == '__main__':
    main()
