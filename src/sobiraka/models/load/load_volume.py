import re
from importlib.resources import files
from math import inf

import panflute
from utilspie.collectionsutils import frozendict

from sobiraka.models import FileSystem, NamingScheme, Volume
from sobiraka.models.config import CombinedToc, Config, Config_Content, Config_HighlightJS, Config_Latex, \
    Config_Latex_HeadersTransform, Config_PDF, Config_Pagefind_Translations, Config_Paths, Config_Pdf_Highlight, \
    Config_Prism, Config_Prover, Config_Prover_Dictionaries, Config_Pygments, Config_Search_LinkTarget, Config_Web, \
    Config_Web_Highlight, Config_Web_Search, SearchIndexerName
from sobiraka.utils import AbsolutePath, Apostrophe, QuotationMark, RelativePath, convert_or_none, expand_vars


def load_volume(lang: str | None, codename: str, volume_data: dict, fs: FileSystem) -> Volume:
    def _(_keys, _default=None):
        try:
            _result = volume_data
            for key in _keys.split('.'):
                _result = _result[key]
            return _result
        except KeyError:
            return _default

    def _expand(_value):
        if isinstance(_value, str):
            return expand_vars(_value, lang=lang, codename=codename)
        if isinstance(_value, (list, tuple)):
            return tuple(expand_vars(_v, lang=lang, codename=codename) for _v in _value)
        if isinstance(_value, (dict, frozendict)):
            return frozendict({_k: expand_vars(_v, lang=lang, codename=codename) for _k, _v in _value.items()})
        return _value

    return Volume(lang, codename, Config(
        title=_('title'),
        paths=Config_Paths(
            root=RelativePath(_expand(_('paths.root', '.'))),
            include=tuple(_expand(_('paths.include', ['**/*']))),
            exclude=tuple(_expand(_('paths.exclude', ''))),
            naming_scheme=convert_or_none(NamingScheme, _('paths.naming_scheme')) or NamingScheme(),
            resources=convert_or_none(RelativePath, _expand(_('paths.resources'))),
            partials=convert_or_none(RelativePath, _expand(_('paths.partials'))),
        ),
        content=Config_Content(
            numeration=_('content.numeration', False),
        ),
        web=Config_Web(
            prefix=_expand(_('web.prefix', '$AUTOPREFIX')),
            resources_prefix=_expand(_('web.resources_prefix', '_resources')),
            resources_force_copy=_expand(_('web.resources_force_copy', ())),
            theme=_find_theme_dir(_expand(_('web.theme', 'simple')), fs=fs),
            theme_data=_expand(_('web.theme_data', {})),
            processor=convert_or_none(RelativePath, _expand(_('web.processor'))),
            custom_styles=tuple(map(RelativePath, _expand(_('web.custom_styles', ())))),
            custom_scripts=tuple(map(RelativePath, _expand(_('web.custom_scripts', ())))),
            toc_depth=int(re.sub(r'^infinity$', '0', str(_('web.toc_depth', 'infinity')))) or inf,
            combined_toc=CombinedToc(_('web.combined_toc', 'never')),
            search=Config_Web_Search(
                engine=convert_or_none(SearchIndexerName, _('web.search.engine')),
                index_path=_expand(_('web.search.index_path')),
                skip_elements=tuple(getattr(panflute.elements, x) for x in _('web.search.skip_elements', ())),
                link_target=Config_Search_LinkTarget(_('web.search.link_target', 'h1')),
                translations=Config_Pagefind_Translations(**_('web.search.translations', {})),
            ),
            highlight=convert_or_none(_load_web_highlight, _('web.highlight')),
        ),
        latex=Config_Latex(
            header=convert_or_none(RelativePath, _expand(_('latex.header'))),
            theme=_find_theme_dir(_expand(_('latex.theme', 'simple')), fs=fs),
            processor=convert_or_none(RelativePath, _expand(_('latex.processor'))),
            toc=_('latex.toc', True),
            paths=frozendict({k: RelativePath(_expand(v)) for k, v in _('latex.paths', {}).items()}),
            headers_transform=Config_Latex_HeadersTransform.load(_('latex.headers_transform', {})),
        ),
        pdf=Config_PDF(
            theme=_find_theme_dir(_expand(_('pdf.theme', 'sobiraka2025')), fs=fs),
            processor=convert_or_none(RelativePath, _expand(_('pdf.processor'))),
            custom_styles=tuple(map(RelativePath, _expand(_('pdf.custom_styles', ())))),
            toc_depth=int(re.sub(r'^infinity$', '0', str(_('pdf.toc_depth', 'infinity')))) or inf,
            combined_toc=_('pdf.combined_toc', False),
            headers_policy=_('pdf.headers_policy', 'local'),
            highlight=convert_or_none(_load_pdf_highlight, _('pdf.highlight')),
        ),
        prover=Config_Prover(
            dictionaries=Config_Prover_Dictionaries.load(_expand(_('prover.dictionaries', ()))),
            skip_elements=tuple(getattr(panflute.elements, x) for x in _('prover.skip_elements', ())),
            phrases_must_begin_with_capitals=_('prover.phrases_must_begin_with_capitals', False),
            allowed_quotation_marks=tuple(map(QuotationMark.load_list, _('prover.allowed_quotation_marks', ()))),
            allowed_apostrophes=tuple(map(Apostrophe.load, _('prover.allowed_apostrophes', ()))),
        ),
        variables=_expand(_('variables', {})),
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


def _find_theme_dir(name: str, *, fs: FileSystem) -> AbsolutePath:
    theme_dir = RelativePath(name)

    if fs.exists(theme_dir) and fs.is_dir(theme_dir):
        return fs.resolve(theme_dir)

    if len(theme_dir.parts) == 1:
        theme_dir = AbsolutePath(files('sobiraka')) / 'files' / 'themes' / theme_dir
        if theme_dir.exists() and theme_dir.is_dir():
            return theme_dir

    raise FileNotFoundError(name)
