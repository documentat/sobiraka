from pathlib import Path
from textwrap import dedent
from typing import Iterable

import jsonschema
import yaml
from utilspie.collectionsutils import frozendict

from sobiraka.runtime import RT
from .project import Project, Volume
from .project import Volume_Paths, Volume_HTML, Volume_PDF, Volume_Lint, Volume_Lint_Checks

MANIFEST_SCHEMA = yaml.load((RT.FILES / 'sobiraka-project.yaml').read_text(), yaml.SafeLoader)


def load_project(manifest_path: Path) -> Project:
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

    volumes: list[Volume] = []
    for lang, language_data in _normalized_and_merged(manifest, 'languages'):
        for codename, volume_data in _normalized_and_merged(language_data, 'volumes'):
            volumes.append(_load_volume(lang, codename, volume_data, base))

    project = Project(base=base, volumes=tuple(volumes))
    for volume in volumes:
        object.__setattr__(volume, 'project', project)
    return project


def _normalized_and_merged(data: dict, key: str) -> Iterable[tuple[str, dict]]:
    from sobiraka.utils import merge_dicts

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
    from sobiraka.utils import convert_or_none

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

    return Volume(
        codename=codename,
        lang=lang,
        title=_('title'),
        paths=Volume_Paths(
            root=global_path(_('paths.root')),
            resources=global_path(_('paths.resources')),
            include=tuple(_('paths.include', ['**/*'])),
            exclude=tuple(_('paths.exclude', '')),
        ),
        html=Volume_HTML(
            prefix=_('html.prefix'),
            resources_prefix=convert_or_none(global_path, _('html.resources_prefix', '_resources')),
        ),
        pdf=Volume_PDF(
            header=convert_or_none(global_path, _('pdf.header')),
        ),
        lint=Volume_Lint(
            dictionaries=tuple(_('lint.dictionaries', [])),
            exceptions=tuple(global_path(x) for x in _('lint.exceptions', [])),
            checks=Volume_Lint_Checks(**_('lint.checks', {})),
        ),
        variables=frozendict(_('variables', {})),
    )
