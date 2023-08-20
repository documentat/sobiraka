import inspect
from pathlib import Path
from typing import Generic, TypeVar

from sobiraka.models import Project
from sobiraka.models.load import load_project
from sobiraka.processing.abstract import Processor
from .projecttestcase import ProjectTestCase

T = TypeVar('T', bound=Processor)


class ProjectDirTestCase(ProjectTestCase, Generic[T]):
    maxDiff = None

    @property
    def dir(self) -> Path:
        return Path(inspect.getfile(self.__class__)).parent

    def _init_project(self) -> Project:
        return load_project(self.dir / 'project.yaml')
