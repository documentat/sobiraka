from functools import partial
from pathlib import Path
from textwrap import dedent
from typing import Iterable

import jsonschema
import yaml
from utilspie.collectionsutils import frozendict

from sobiraka.runtime import RT
from sobiraka.utils import convert_or_none, merge_dicts
from .config import Config_HTML, Config_Lint, Config_Lint_Checks, Config_PDF, Config_Paths
from .project import Project
from .volume import Volume

MANIFEST_SCHEMA = yaml.safe_load((RT.FILES / 'sobiraka-project.yaml').read_text())


def load_project(manifest_path: Path) -> Project:
    """
    Load a :obj:`.Project` from the YAML file at `manifest_path`.

    The file must be formatted using the schema defined at ``files/sobiraka-project.yaml`` in the sources.
    """
    manifest_path = manifest_path.resolve()
    with manifest_path.open() as manifest_file:
        manifest: dict = yaml.safe_load(manifest_file) or {}
    return load_project_from_dict(manifest, base=manifest_path.parent)


def load_project_from_str(manifest_yaml: str, *, base: Path) -> Project:
    manifest_yaml = dedent(manifest_yaml)
    manifest: dict = yaml.safe_load(manifest_yaml) or {}
    return load_project_from_dict(manifest, base=base)


def load_project_from_dict(manifest: dict, *, base: Path) -> Project:
    if manifest:
        jsonschema.validate(manifest, MANIFEST_SCHEMA)

    volumes: dict[str, Volume] = {}
    for lang, language_data in _normalized_and_merged(manifest, 'languages'):
        for codename, volume_data in _normalized_and_merged(language_data, 'volumes'):
            volume = _load_volume(lang, codename, volume_data, base)
            volumes[volume.autoprefix] = volume

    primary_volume = None
    if 'primary' in manifest:
        primary_volume = volumes[manifest['primary']]

    project = Project(base=base,
                      volumes=tuple(volumes.values()),
                      primary_volume=primary_volume)
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


def _load_volume(lang: str | None, codename: str, volume_data: dict, base: Path) -> Volume:
    def _(_keys, _default=None):
        try:
            _result = volume_data
            for key in _keys.split('.'):
                _result = _result[key]
            return _result
        except KeyError:
            return _default

    def global_path(x: str) -> Path:
        return (base / (x or '')).resolve()

    # TODO get defaults directly from the Config_* classes
    return Volume(
        codename=codename,
        lang=lang,
        title=_('title'),
        paths=Config_Paths(
            root=global_path(_('paths.root')),
            resources=global_path(_('paths.resources')),
            include=tuple(_('paths.include', ['**/*'])),
            exclude=tuple(_('paths.exclude', '')),
        ),
        html=Config_HTML(
            prefix=_('html.prefix', '$AUTOPREFIX'),
            resources_prefix=_('html.resources_prefix', '_resources'),
            resources_force_copy=_('html.resources_force_copy', ()),
            theme=convert_or_none(partial(_load_html_theme, base=base), _('html.theme'))
                  or RT.FILES / 'themes' / 'material',
            theme_data=_('html.theme_data', {}),
        ),
        pdf=Config_PDF(
            header=convert_or_none(global_path, _('pdf.header')),
        ),
        lint=Config_Lint(
            dictionaries=tuple(_('lint.dictionaries', [])),
            exceptions=tuple(global_path(x) for x in _('lint.exceptions', [])),
            checks=Config_Lint_Checks(**_('lint.checks', {})),
        ),
        variables=frozendict(_('variables', {})),
    )


def _load_html_theme(name: str, *, base: Path) -> Path:
    theme_dir = base / name
    if theme_dir.exists() and theme_dir.is_dir():
        return theme_dir
    if '/' not in name:
        theme_dir = RT.FILES / 'themes' / name
        if theme_dir.exists() and theme_dir.is_dir():
            return theme_dir
    raise FileNotFoundError(base / name)
