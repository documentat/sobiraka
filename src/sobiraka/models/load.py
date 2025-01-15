import re
from importlib.resources import files
from math import inf
from textwrap import dedent
from typing import Iterable

import panflute
import yaml
from jsonschema.validators import Draft202012Validator
from utilspie.collectionsutils import frozendict

from sobiraka.models.config import Config_Prover_Dictionaries
from sobiraka.utils import AbsolutePath, QuotationMark, RelativePath, convert_or_none, get_default, merge_dicts
from .config import CombinedToc, Config, Config_Content, Config_HighlightJS, Config_Latex, Config_Latex_Headers, \
    Config_PDF, Config_Pagefind_Translations, Config_Paths, Config_Pdf_Highlight, Config_Prism, Config_Prover, \
    Config_Pygments, Config_Search_LinkTarget, Config_Web, Config_Web_Highlight, Config_Web_Search, SearchIndexerName
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
        Draft202012Validator(manifest).validate(MANIFEST_SCHEMA)

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
        web=Config_Web(
            prefix=_('web.prefix', '$AUTOPREFIX'),
            resources_prefix=_('web.resources_prefix', '_resources'),
            theme=_find_theme_dir(_('web.theme', 'simple'), fs=fs),
            theme_data=_('web.theme_data', {}),
            processor=convert_or_none(RelativePath, _('web.processor')),
            custom_styles=tuple(map(RelativePath, _('web.custom_styles', ()))),
            custom_scripts=tuple(map(RelativePath, _('web.custom_scripts', ()))),
            toc_depth=int(re.sub(r'^infinity$', '0', str(_('web.toc_depth', 'infinity')))) or inf,
            combined_toc=CombinedToc(_('web.combined_toc', 'never')),
            search=Config_Web_Search(
                engine=convert_or_none(SearchIndexerName, _('web.search.engine')),
                index_path=_('web.search.index_path'),
                skip_elements=tuple(getattr(panflute.elements, x) for x in _('web.search.skip_elements', ())),
                link_target=Config_Search_LinkTarget(_('web.search.link_target', 'h1')),
                translations=Config_Pagefind_Translations(**_('web.search.translations', {})),
            ),
            highlight=convert_or_none(_load_web_highlight, _('web.highlight')),
        ),
        latex=Config_Latex(
            header=convert_or_none(RelativePath, _('latex.header')),
            theme=_find_theme_dir(_('latex.theme', 'simple'), fs=fs),
            processor=convert_or_none(RelativePath, _('latex.processor')),
            toc=_('latex.toc', True),
            paths=frozendict({k: RelativePath(v) for k, v in _('latex.paths', {}).items()}),
            headers=Config_Latex_Headers(
                by_class=frozendict(_('latex.headers.by_class', {})),
                by_global_level=_load_latex_headers_by_global_level(_('latex.headers.by_global_level', {})),
                by_page_level=frozendict({int(k): v for k, v in _('latex.headers.by_page_level', {}).items()}),
                by_element=frozendict(_('latex.headers.by_element', {})),
            )
        ),
        pdf=Config_PDF(
            theme=_find_theme_dir(_('pdf.theme', 'printable'), fs=fs),
            processor=convert_or_none(RelativePath, _('pdf.processor')),
            custom_styles=tuple(map(RelativePath, _('pdf.custom_styles', ()))),
            toc_depth=int(re.sub(r'^infinity$', '0', str(_('pdf.toc_depth', 'infinity')))) or inf,
            combined_toc=_('pdf.combined_toc', False),
            highlight=convert_or_none(_load_pdf_highlight, _('pdf.highlight')),
        ),
        prover=Config_Prover(
            dictionaries=Config_Prover_Dictionaries.load(_('prover.dictionaries', ())),
            skip_elements=tuple(getattr(panflute.elements, x) for x in _('prover.skip_elements', ())),
            phrases_must_begin_with_capitals=_('prover.phrases_must_begin_with_capitals', False),
            allowed_quotation_marks=tuple(map(QuotationMark.load_list, _('prover.allowed_quotation_marks', ()))),
        ),
        variables=frozendict(_('variables', {})),
    ))


def _load_web_highlight(data: str | dict[str, dict]) -> Config_Web_Highlight:
    if isinstance(data, str):
        engine, config = data, {}
    else:
        assert len(data) == 1
        engine, config = next(iter(data.items()))

    match engine:
        case 'highlightjs':
            return Config_HighlightJS.load(config or {})
        case 'prism':
            return Config_Prism.load(config or {})
        case 'pygments':
            return Config_Pygments(**(config or {}))


def _load_pdf_highlight(data: str | dict[str, dict]) -> Config_Pdf_Highlight:
    if isinstance(data, str):
        engine, config = data, {}
    else:
        assert len(data) == 1
        engine, config = next(iter(data.items()))

    match engine:
        case 'pygments':
            return Config_Pygments(**(config or {}))


def _load_latex_headers_by_global_level(values: dict[str, str]) -> frozendict[int, str]:
    if values:
        return frozendict({int(k): v for k, v in values.items()})
    return get_default(Config_Latex_Headers, 'by_global_level')


def _find_theme_dir(name: str, *, fs: FileSystem) -> AbsolutePath:
    theme_dir = RelativePath(name)

    if fs.exists(theme_dir) and fs.is_dir(theme_dir):
        return fs.resolve(theme_dir)

    if len(theme_dir.parts) == 1:
        theme_dir = AbsolutePath(files('sobiraka')) / 'files' / 'themes' / theme_dir
        if theme_dir.exists() and theme_dir.is_dir():
            return theme_dir

    raise FileNotFoundError(name)
