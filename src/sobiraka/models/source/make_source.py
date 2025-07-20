from __future__ import annotations

from typing import TYPE_CHECKING

from sobiraka.utils import RelativePath
from ..filesystem import FileSystem

if TYPE_CHECKING:
    from sobiraka.models import Document, Source


def make_source(document: Document, path_in_project: RelativePath, *, parent: Source | None) -> Source:
    from sobiraka.models.source import NAV_FILENAME, SourceDirectory, SourceFile, SourceNav

    fs: FileSystem = document.project.fs

    if not fs.is_dir(path_in_project):
        return SourceFile(document, path_in_project, parent=parent)

    if fs.exists(path_in_project / NAV_FILENAME):
        return SourceNav(document, path_in_project, parent=parent)

    return SourceDirectory(document, path_in_project, parent=parent)
