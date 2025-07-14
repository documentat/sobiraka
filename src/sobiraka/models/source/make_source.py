from __future__ import annotations

from typing import TYPE_CHECKING

from sobiraka.utils import RelativePath
from ..filesystem import FileSystem

if TYPE_CHECKING:
    from sobiraka.models import Source, Volume


def make_source(volume: Volume, path_in_project: RelativePath, *, parent: Source | None) -> Source:
    from sobiraka.models.source import SourceDirectory
    from sobiraka.models.source import SourceFile
    from sobiraka.models.source import NAV_FILENAME, SourceNav

    fs: FileSystem = volume.project.fs

    if not fs.is_dir(path_in_project):
        return SourceFile(volume, path_in_project, parent=parent)

    if fs.exists(path_in_project / NAV_FILENAME):
        return SourceNav(volume, path_in_project, parent=parent)

    return SourceDirectory(volume, path_in_project, parent=parent)
