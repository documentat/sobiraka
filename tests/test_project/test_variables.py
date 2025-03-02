from unittest import TestCase

from utilspie.collectionsutils import frozendict

from helpers import FakeFileSystem
from sobiraka.models.load import load_project_from_str
from sobiraka.utils import AbsolutePath, RelativePath

DATA = '''
languages:
  en:
    volumes:
      mydoc:
        paths:
          root: src/$VOLUME
          include: ['**/*.$LANG.md']
          exclude: ['**/.*.$LANG.md']
          resources: resources/$LANG
          partials: partials/$LANG

        web:
          prefix: docs-$LANG
          resources_prefix: static/$LANG
          theme: themes/$VOLUME
          theme_data:
            logo: logo-$VOLUME-$LANG.png
          processor: processor_$VOLUME.py
          custom_styles:
            - style.$VOLUME.css
          custom_scripts:
            - script.$VOLUME.js
          search:
            index_path: index/$VOLUME-$LANG

        latex:
          header: headers-$VOLUME.sty
          theme: themes/$VOLUME
          processor: processor_$VOLUME.py
          paths:
            fonts: fonts/$VOLUME

        pdf:
          theme: themes/$VOLUME
          processor: processor_$VOLUME.py
          custom_styles:
            - style.$VOLUME.css
        
        prover:
          dictionaries:
            - dictionaries/$LANG.dic
        
        variables:
          foo: bar-$LANG
'''


class TestVariables(TestCase):
    def setUp(self):
        fs = FakeFileSystem({
            RelativePath('themes/mydoc/extension.py'): '',
        })
        project = load_project_from_str(DATA, fs=fs)
        self.config = project.get_volume().config

    def test_paths(self):
        with self.subTest('root'):
            self.assertEqual(RelativePath('src/mydoc'), self.config.paths.root)
        with self.subTest('include'):
            self.assertEqual(('**/*.en.md',), self.config.paths.include)
        with self.subTest('exclude'):
            self.assertEqual(('**/.*.en.md',), self.config.paths.exclude)
        with self.subTest('resources'):
            self.assertEqual(RelativePath('resources/en'), self.config.paths.resources)
        with self.subTest('partials'):
            self.assertEqual(RelativePath('partials/en'), self.config.paths.partials)

    def test_web(self):
        with self.subTest('prefix'):
            self.assertEqual('docs-en', self.config.web.prefix)
        with self.subTest('resources_prefix'):
            self.assertEqual('static/en', self.config.web.resources_prefix)
        with self.subTest('theme'):
            self.assertEqual(AbsolutePath('/FAKE/themes/mydoc'), self.config.web.theme)
        with self.subTest('theme_data'):
            self.assertEqual(frozendict({'logo': 'logo-mydoc-en.png'}), self.config.web.theme_data)
        with self.subTest('processor'):
            self.assertEqual(RelativePath('processor_mydoc.py'), self.config.web.processor)
        with self.subTest('custom_styles'):
            self.assertEqual((RelativePath('style.mydoc.css'),), self.config.web.custom_styles)
        with self.subTest('custom_scripts'):
            self.assertEqual((RelativePath('script.mydoc.js'),), self.config.web.custom_scripts)
        with self.subTest('index_path'):
            self.assertEqual('index/mydoc-en', self.config.web.search.index_path)

    def test_latex(self):
        with self.subTest('header'):
            self.assertEqual(RelativePath('headers-mydoc.sty'), self.config.latex.header)
        with self.subTest('theme'):
            self.assertEqual(AbsolutePath('/FAKE/themes/mydoc'), self.config.latex.theme)
        with self.subTest('processor'):
            self.assertEqual(RelativePath('processor_mydoc.py'), self.config.latex.processor)
        with self.subTest('paths'):
            self.assertEqual(frozendict({'fonts': RelativePath('fonts/mydoc')}), self.config.latex.paths)

    def test_pdf(self):
        with self.subTest('theme'):
            self.assertEqual(AbsolutePath('/FAKE/themes/mydoc'), self.config.pdf.theme)
        with self.subTest('processor'):
            self.assertEqual(RelativePath('processor_mydoc.py'), self.config.pdf.processor)
        with self.subTest('custom_styles'):
            self.assertEqual((RelativePath('style.mydoc.css'),), self.config.pdf.custom_styles)

    def test_prover(self):
        with self.subTest('dictionaries'):
            self.assertEqual((RelativePath('dictionaries/en.dic'),),
                             self.config.prover.dictionaries.hunspell_dictionaries)

    def test_variables(self):
        self.assertEqual(frozendict({'foo': 'bar-en'}), self.config.variables)
