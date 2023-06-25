from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import IntEnum, auto
from itertools import groupby
from pathlib import Path

import git
from git import Commit, Repo
from more_itertools import unique_justseen

from sobiraka.models import Page, Project, Version
from sobiraka.models.load import load_project_from_str


def changelog(manifest_path: Path, rev1: str, rev2: str) -> int:
    # pylint: disable=too-many-locals

    repo = Repo(manifest_path.parent)
    commit1 = repo.commit(rev1)
    commit2 = repo.commit(rev2)

    project1 = load_project_from_revision(commit1, manifest_path.parts[-1])
    project2 = load_project_from_revision(commit2, manifest_path.parts[-1])

    result: list[ChangeLogItem] = []

    for diff in commit1.diff(commit2):
        try:
            page1 = load_page_from_blob(project1, Path(diff.a_path), diff.a_blob)
            text1 = page1.text
            v1 = page1.meta.version

            page2 = load_page_from_blob(project2, Path(diff.b_path), diff.b_blob)
            text2 = page2.text
            v2 = page2.meta.version

        except KeyError:
            continue

        status = ChangeLogItemStatus.choose(v1, v2, is_text_modified=text1 != text2)
        if status:
            result.append(ChangeLogItem(status, page2.path_in_project, v1, v2))

    result.sort()

    for status, items in groupby(result, key=lambda x: x.status):
        print(f'{status}:', file=sys.stderr)
        for item in items:
            versions_list = ' -> '.join(map(str, filter(None, unique_justseen((item.v1, item.v2)))))
            print(f'  {item.path} ({versions_list})', file=sys.stderr)

    return 0


def load_project_from_revision(commit: Commit, manifest_name: str) -> Project:
    manifest_blob = commit.tree / manifest_name
    manifest_yaml = manifest_blob.data_stream.read().decode('utf-8')
    project = load_project_from_str(manifest_yaml, base=Path(commit.repo.working_dir))
    return project


def load_page_from_blob(project: Project, path_in_project: Path, blob: git.Blob) -> Page:
    volume = project.get_volume_by_path(path_in_project)
    path_in_volume = path_in_project.relative_to(volume.relative_root)
    text = blob.data_stream.read().decode('utf-8')
    return Page(volume, path_in_volume, text)


@dataclass(order=True)
class ChangeLogItem:
    status: ChangeLogItemStatus
    path: Path
    v1: Version
    v2: Version


class ChangeLogItemStatus(IntEnum):
    VERSION_UPGRADED = auto()
    TEXT_UPGRADED = auto()
    BOTH_UPGRADED = auto()
    VERSION_DOWNGRADED = auto()
    BOTH_DOWNGRADED = auto()
    VERSION_APPEARED = auto()
    VERSION_DISAPPEARED = auto()

    def __str__(self):
        return {
            ChangeLogItemStatus.VERSION_UPGRADED: 'Version upgraded',
            ChangeLogItemStatus.TEXT_UPGRADED: 'Text upgraded',
            ChangeLogItemStatus.BOTH_UPGRADED: 'Both upgraded',
            ChangeLogItemStatus.VERSION_DOWNGRADED: 'Version downgraded',
            ChangeLogItemStatus.BOTH_DOWNGRADED: 'Both downgraded',
            ChangeLogItemStatus.VERSION_APPEARED: 'Version appeared',
            ChangeLogItemStatus.VERSION_DISAPPEARED: 'Version disappeared',
        }[self]

    @staticmethod
    def choose(v1: Version, v2: Version, *, is_text_modified: bool) -> ChangeLogItemStatus | None:
        # pylint: disable=too-many-return-statements, no-else-return

        match v1, v2:
            case None, None:
                return None
            case None, Version():
                return ChangeLogItemStatus.VERSION_APPEARED
            case Version(), None:
                return ChangeLogItemStatus.VERSION_DISAPPEARED

        if is_text_modified:
            if v1 < v2:
                return ChangeLogItemStatus.BOTH_UPGRADED
            if v1 > v2:
                return ChangeLogItemStatus.BOTH_DOWNGRADED
            return ChangeLogItemStatus.TEXT_UPGRADED
        else:
            if v1 < v2:
                return ChangeLogItemStatus.VERSION_UPGRADED
            if v1 > v2:
                return ChangeLogItemStatus.VERSION_DOWNGRADED
            raise ValueError('Maybe I use git diff incorrectly.')
