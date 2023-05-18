from typing import TypeVar, Generic

from sobiraka.models import Project
from sobiraka.models.load import load_project
from sobiraka.processing.abstract import Processor
from .projecttestcase import ProjectTestCase

T = TypeVar('T', bound=Processor)


class ProjectDirTestCase(ProjectTestCase, Generic[T]):
    maxDiff = None

    def _init_project(self) -> Project:
        return load_project(self.dir / 'project.yaml')