from __future__ import annotations

from typing import overload

from helpers import FakeFileSystem
from helpers.fakefilesystem import PseudoFiles
from sobiraka.models import Document, Project
from sobiraka.models.config import Config, Config_Paths
from sobiraka.utils import RelativePath


class FakeProject(Project):
    fs: FakeFileSystem

    def __init__(self, documents: dict[str, FakeDocument]):
        fs = FakeFileSystem()
        super().__init__(fs, tuple(documents.values()), None)

        for root, document in documents.items():
            root = RelativePath(root)

            document.codename = root.name

            fs.add_files(document.pseudofiles, parent=root)
            delattr(document, 'pseudofiles')

            if document.config is None:
                document.config = Config(paths=Config_Paths(root=root))


class FakeDocument(Document):
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
