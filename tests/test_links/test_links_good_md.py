import unittest

from test_links.abstracttestlinksgood_html import AbstractTestLinksGoodHtml
from test_links.abstracttestlinksgood import AbstractTestLinksGood

SOURCES = {}

SOURCES['document0.md'] = '''
# Welcome
- [Document 1](sub/document1.md)
- [Document 2](sub/subsub/document2.md)
- [Document 3](sub/subsub/document3.md), specifically [section 1](sub/subsub/document3.md#sect1) and [section 2](sub/subsub/document3.md#section-2)
- [Document 4](sub/subsub/subsubsub/document4.md)

BTW, here's [some website](https://example.com/).
'''

SOURCES['sub/document1.md'] = '''
# Document 1
- [Document 0](../document0.md)
- [Document 2](subsub/document2.md)
- [Document 3](subsub/document3.md)
- [Document 4](subsub/subsubsub/document4.md)
'''

SOURCES['sub/subsub/document2.md'] = '''
# Document 2
- [Document 0](../../document0.md)
- [Document 1](../document1.md)
- [Document 3](document3.md)
- [Document 4](subsubsub/document4.md)
'''

SOURCES['sub/subsub/document3.md'] = '''
# Document 3
- [Document 0](../../document0.md)
- [Document 1](../document1.md)
- [Document 2](document2.md)
- [Document 4](subsubsub/document4.md)

## Section 1 {#sect1}
See [Section 2](#section-2).

## Section 2
See [Section 1](#sect1).
'''

SOURCES['sub/subsub/subsubsub/document4.md'] = '''
# Document 4
- [Document 0](../../../document0.md)
- [Document 1](../../document1.md)
- [Document 2](../document2.md)
- [Document 3](../document3.md)
'''


class TestLinksGood_MD(AbstractTestLinksGood):
    SOURCES = SOURCES


class TestLinksGoodHtml_MD(AbstractTestLinksGoodHtml):
    SOURCES = SOURCES


del AbstractTestLinksGood, AbstractTestLinksGoodHtml

if __name__ == '__main__':
    unittest.main()
