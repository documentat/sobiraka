import inspect
from typing import Generic, TypeVar

from sobiraka.models import Project
from sobiraka.models.load import load_project
from sobiraka.processing.abstract import Builder
from sobiraka.utils import AbsolutePath
from .projecttestcase import ProjectTestCase

T = TypeVar('T', bound=Builder)


class ProjectDirTestCase(ProjectTestCase, Generic[T]):
    maxDiff = None

    @property
    def dir(self) -> AbsolutePath:
        return AbsolutePath(inspect.getfile(self.__class__)).parent

    def _init_project(self) -> Project:
        return load_project(self.dir / 'sobiraka.yaml')
