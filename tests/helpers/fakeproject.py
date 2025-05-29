from __future__ import annotations

from typing import overload

from helpers import FakeFileSystem
from helpers.fakefilesystem import PseudoFiles
from sobiraka.models import Project, Volume
from sobiraka.models.config import Config, Config_Paths
from sobiraka.utils import RelativePath


class FakeProject(Project):
    fs: FakeFileSystem

    def __init__(self, volumes: dict[str, FakeVolume]):
        fs = FakeFileSystem()
        super().__init__(fs, tuple(volumes.values()), None)

        for root, volume in volumes.items():
            root = RelativePath(root)

            volume.codename = root.name

            fs.add_files(volume.pseudofiles, parent=root)
            delattr(volume, 'pseudofiles')

            if volume.config is None:
                volume.config = Config(paths=Config_Paths(root=root))


class FakeVolume(Volume):
    sources = None

    @overload
    def __init__(self, config: Config, pseudofiles: PseudoFiles):
        ...

    @overload
    def __init__(self, pseudofiles: PseudoFiles):
        ...

    def __init__(self, *args):
        match args:
            case Config() as config, dict() as pseudofiles:
                super().__init__(None, None, config)
                self.pseudofiles = pseudofiles

            case dict() as pseudofiles,:
                super().__init__(None, None, Config(paths=Config_Paths(root=RelativePath('src'))))
                self.pseudofiles = pseudofiles

            case _:
                raise TypeError(args)
