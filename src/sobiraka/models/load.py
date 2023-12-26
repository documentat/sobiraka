import re
from math import inf
from pathlib import Path
from textwrap import dedent
from typing import Iterable

import jsonschema
import yaml
from utilspie.collectionsutils import frozendict

from sobiraka.runtime import RT
from sobiraka.utils import convert_or_none, merge_dicts
from .config import CombinedToc, Config, Config_Content, Config_HTML, Config_Lint, Config_Lint_Checks, Config_PDF, \
    Config_Paths
from .filesystem import FileSystem, RealFileSystem
from .namingscheme import NamingScheme
from .project import Project
from .volume import Volume

MANIFEST_SCHEMA = yaml.safe_load((RT.FILES / 'sobiraka-project.yaml').read_text())


def load_project(manifest_path: Path) -> Project:
    """
    Load a :obj:`.Project` from the YAML file at `manifest_path`.

    The file must be formatted using the schema defined at ``files/sobiraka-project.yaml`` in the sources.
    """
    manifest_path = manifest_path.resolve()
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
            root=Path(_('paths.root', '.')),
            include=tuple(_('paths.include', ['**/*'])),
            exclude=tuple(_('paths.exclude', '')),
            naming_scheme=convert_or_none(NamingScheme, _('paths.naming_schema')) or NamingScheme(),
            resources=convert_or_none(Path, _('paths.resources')),
            partials=convert_or_none(Path, _('paths.partials')),
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
            toc_expansion=int(re.sub(r'^infinity$', '0', str(_('html.toc_expansion', 'infinity')))) or inf,
            combined_toc=CombinedToc(_('html.combined_toc', 'never')),
        ),
        pdf=Config_PDF(
            header=convert_or_none(Path, _('pdf.header')),
            theme=_find_theme_dir(_('pdf.theme', 'simple'), fs=fs),
            toc=_('pdf.toc', True),
        ),
        lint=Config_Lint(
            dictionaries=tuple(_('lint.dictionaries', [])),
            exceptions=tuple(map(Path, _('lint.exceptions', []))),
            checks=Config_Lint_Checks(**_('lint.checks', {})),
        ),
        variables=frozendict(_('variables', {})),
    ))


def _find_theme_dir(name: str, *, fs: FileSystem) -> Path:
    theme_dir = Path(name)
    assert not theme_dir.is_absolute()

    if fs.exists(theme_dir) and fs.is_dir(theme_dir):
        return theme_dir

    if len(theme_dir.parts) == 1:
        theme_dir = RT.FILES / 'themes' / theme_dir
        if theme_dir.exists() and theme_dir.is_dir():
            return theme_dir

    raise FileNotFoundError(name)
