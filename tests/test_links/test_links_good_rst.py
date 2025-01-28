import unittest

from test_links.abstracttestlinksgood import AbstractTestLinksGood
from test_links.abstracttestlinksgood_html import AbstractTestLinksGoodHtml

SOURCES = {}

SOURCES['document0.rst'] = '''
Welcome
=======
- :doc:`Document 1 <sub/document1.rst>`
- :doc:`Document 2 <sub/subsub/document2.rst>`
- :doc:`Document 3 <sub/subsub/document3.rst>`, specifically :doc:`section 1 <sub/subsub/document3.rst#sect1>` and :doc:`section 2 <sub/subsub/document3.rst#section-2>`
- :doc:`Document 4 <sub/subsub/subsubsub/document4.rst>`

BTW, here's `some website <https://example.com/>`__.
'''

SOURCES['sub/document1.rst'] = '''
Document 1
==========
- :doc:`Document 0 <../document0.rst>`
- :doc:`Document 2 <subsub/document2.rst>`
- :doc:`Document 3 <subsub/document3.rst>`
- :doc:`Document 4 <subsub/subsubsub/document4.rst>`
'''

SOURCES['sub/subsub/document2.rst'] = '''
Document 2
==========
- :doc:`Document 0 <../../document0.rst>`
- :doc:`Document 1 <../document1.rst>`
- :doc:`Document 3 <document3.rst>`
- :doc:`Document 4 <subsubsub/document4.rst>`
'''

SOURCES['sub/subsub/document3.rst'] = '''
Document 3
==========
- :doc:`Document 0 <../../document0.rst>`
- :doc:`Document 1 <../document1.rst>`
- :doc:`Document 2 <document2.rst>`
- :doc:`Document 4 <subsubsub/document4.rst>`

.. _sect1:

Section 1
---------
See :doc:`Section 2 <#section-2>`.

Section 2
---------
See :doc:`Section 1 <#sect1>`.
'''

SOURCES['sub/subsub/subsubsub/document4.rst'] = '''
Document 4
==========
- :doc:`Document 0 <../../../document0.rst>`
- :doc:`Document 1 <../../document1.rst>`
- :doc:`Document 2 <../document2.rst>`
- :doc:`Document 3 <../document3.rst>`
'''


class TestLinksGood_RST(AbstractTestLinksGood):
    SOURCES = SOURCES


class TestLinksGoodHtml_RST(AbstractTestLinksGoodHtml):
    SOURCES = SOURCES


del AbstractTestLinksGood, AbstractTestLinksGoodHtml

if __name__ == '__main__':
    unittest.main()
