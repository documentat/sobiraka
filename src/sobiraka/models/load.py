import re
from importlib.resources import files
from math import inf
from textwrap import dedent
from typing import Iterable

import jsonschema
import panflute
import yaml
from utilspie.collectionsutils import frozendict

from sobiraka.utils import AbsolutePath, RelativePath, convert_or_none, merge_dicts
from .config import CombinedToc, Config, Config_Content, Config_HTML, Config_HTML_Search, Config_Latex, Config_Lint, \
    Config_Lint_Checks, Config_Pagefind_Translations, Config_Paths, Config_Search_LinkTarget, Config_WeasyPrint, \
    SearchIndexerName
from .filesystem import FileSystem, RealFileSystem
from .namingscheme import NamingScheme
from .project import Project
from .volume import Volume

MANIFEST_SCHEMA = yaml.safe_load((files('sobiraka') / 'files' / 'sobiraka-project.yaml').read_text())


def load_project(manifest_path: AbsolutePath) -> Project:
    """
    Load a :obj:`.Project` from the YAML file at `manifest_path`.

    The file must be formatted using the schema defined at ``files/sobiraka-project.yaml`` in the sources.
    """
    with manifest_path.open(encoding='utf-8') as manifest_file:
        manifest: dict = yaml.safe_load(manifest_file) or {}
    fs = RealFileSystem(manifest_path.parent)
    project = load_project_from_dict(manifest, fs=fs)
    project.manifest_path = manifest_path
    return project


def load_project_from_str(manifest_yaml: str, *, fs: FileSystem) -> Project:
    manifest_yaml = dedent(manifest_yaml)
    manifest: dict = yaml.safe_load(manifest_yaml) or {}
    return load_project_from_dict(manifest, fs=fs)


def load_project_from_dict(manifest: dict, *, fs: FileSystem) -> Project:
    if manifest:
        jsonschema.validate(manifest, MANIFEST_SCHEMA)

    volumes: list[Volume] = []
    for lang, language_data in _normalized_and_merged(manifest, 'languages'):
        for codename, volume_data in _normalized_and_merged(language_data, 'volumes'):
            volumes.append(_load_volume(lang, codename, volume_data, fs))

    project = Project(fs, tuple(volumes))
    project.primary_language = manifest.get('primary_language') or volumes[0].lang
    return project


def _normalized_and_merged(data: dict, key: str) -> Iterable[tuple[str, dict]]:
    if key not in data:
        yield None, data
    elif list(data[key]) == ['DEFAULT']:
        yield None, data[key]['DEFAULT']
    elif 'DEFAULT' in data[key]:
        defaults = data[key].pop('DEFAULT')
        for k, v in data[key].items():
            v = merge_dicts(defaults, v)
            yield k, v
    else:
        yield from data[key].items()


def _load_volume(lang: str | None, codename: str, volume_data: dict, fs: FileSystem) -> Volume:
    def _(_keys, _default=None):
        try:
            _result = volume_data
            for key in _keys.split('.'):
                _result = _result[key]
            return _result
        except KeyError:
            return _default

    return Volume(lang, codename, Config(
        title=_('title'),
        paths=Config_Paths(
            root=RelativePath(_('paths.root', '.')),
            include=tuple(_('paths.include', ['**/*'])),
            exclude=tuple(_('paths.exclude', '')),
            naming_scheme=convert_or_none(NamingScheme, _('paths.naming_scheme')) or NamingScheme(),
            resources=convert_or_none(RelativePath, _('paths.resources')),
            partials=convert_or_none(RelativePath, _('paths.partials')),
        ),
        content=Config_Content(
            numeration=_('content.numeration', False),
        ),
        html=Config_HTML(
            prefix=_('html.prefix', '$AUTOPREFIX'),
            resources_prefix=_('html.resources_prefix', '_resources'),
            resources_force_copy=_('html.resources_force_copy', ()),
            theme=_find_theme_dir(_('html.theme', 'simple'), fs=fs),
            theme_data=_('html.theme_data', {}),
            toc_depth=int(re.sub(r'^infinity$', '0', str(_('html.toc_depth', 'infinity')))) or inf,
            combined_toc=CombinedToc(_('html.combined_toc', 'never')),
            search=Config_HTML_Search(
                engine=convert_or_none(SearchIndexerName, _('html.search.engine')),
                index_path=_('html.search.index_path'),
                skip_elements=tuple(getattr(panflute.elements, x) for x in _('html.search.skip_elements', ())),
                link_target=Config_Search_LinkTarget(_('html.search.link_target', 'h1')),
                translations=Config_Pagefind_Translations(**_('html.search.translations', {})),
            ),
        ),
        latex=Config_Latex(
            header=convert_or_none(RelativePath, _('latex.header')),
            theme=_find_theme_dir(_('latex.theme', 'simple'), fs=fs),
            toc=_('latex.toc', True),
            paths=frozendict({k: RelativePath(v) for k, v in _('latex.paths', {}).items()}),
        ),
        weasyprint=Config_WeasyPrint(
            theme=_find_theme_dir(_('weasyprint.theme', 'printable'), fs=fs),
        ),
        lint=Config_Lint(
            dictionaries=tuple(_('lint.dictionaries', [])),
            exceptions=tuple(map(RelativePath, _('lint.exceptions', []))),
            checks=Config_Lint_Checks(**_('lint.checks', {})),
        ),
        variables=frozendict(_('variables', {})),
    ))


def _find_theme_dir(name: str, *, fs: FileSystem) -> AbsolutePath:
    theme_dir = RelativePath(name)

    if fs.exists(theme_dir) and fs.is_dir(theme_dir):
        return fs.resolve(theme_dir)

    if len(theme_dir.parts) == 1:
        theme_dir = AbsolutePath(files('sobiraka')) / 'files' / 'themes' / theme_dir
        if theme_dir.exists() and theme_dir.is_dir():
            return theme_dir

    raise FileNotFoundError(name)
