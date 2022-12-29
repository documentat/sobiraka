from pathlib import Path
from unittest import main, skip, TestCase

from sobiraka.models import Href, UrlHref


@skip('')
class TestHref(TestCase):
    def test_abstract(self):
        with self.assertRaises(TypeError):
            Href()

    def test_url_href(self):
        for url in ('https://example.com/', 'mailto:user@example.com'):
            with self.subTest(url):
                href = Href.from_string(url)
                self.assertIsInstance(href, UrlHref)
                self.assertEqual(href.url, url)
                self.assertEqual(str(href), url)

    def test_doc_href(self):
        for string, expected_str, expected_target, expected_anchor in (
                ('page.md', 'page.md', 'page.md', None),
                ('#', '', None, None),
                ('#anchor', '#anchor', None, 'anchor'),
                ('page.md#anchor', 'page.md#anchor', 'page.md', 'anchor'),
                ('page.md#', 'page.md', 'page.md', None),
        ):
            with self.subTest(string):
                href = Href.from_string(string)
                self.assertIsInstance(href, DocHref)
                self.assertEqual(href.target, Path(expected_target) if expected_target is not None else None)
                self.assertEqual(href.anchor, expected_anchor)
                self.assertEqual(str(href), expected_str)


if __name__ == '__main__':
    main()
