from importlib.resources import files
from textwrap import dedent
from typing import Iterable

import yaml
from jsonschema.validators import Draft202012Validator

from sobiraka.utils import AbsolutePath, merge_dicts
from .load_document import load_document
from ..document import Document
from ..filesystem import FileSystem, RealFileSystem
from ..project import Project

SCHEMA = yaml.safe_load((files('sobiraka') / 'files' / 'sobiraka-project.yaml').read_text())


def load_project(manifest_path: AbsolutePath) -> Project:
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
        Draft202012Validator(manifest).validate(SCHEMA)

    documents: list[Document] = []
    for lang, language_data in _normalized_and_merged(manifest, 'languages'):
        for codename, document_data in _normalized_and_merged(language_data, 'documents'):
            documents.append(load_document(lang, codename, document_data, fs))

    primary_language = manifest.get('primary_language') or documents[0].lang

    return Project(fs, tuple(documents), primary_language)


def _normalized_and_merged(data: dict, key: str) -> Iterable[tuple[str | None, dict]]:
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
