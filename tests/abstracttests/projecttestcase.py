from abc import abstractmethod, ABCMeta
from asyncio import gather
from inspect import getfile
from pathlib import Path
from typing import Any, Generic, Iterable, TypeVar
from unittest import IsolatedAsyncioTestCase, SkipTest

from sobiraka.models import Project, Page
from sobiraka.processing.abstract import Processor

T = TypeVar('T', bound=Processor)


class ProjectTestCase(IsolatedAsyncioTestCase, Generic[T], metaclass=ABCMeta):
    maxDiff = None

    async def asyncSetUp(self):
        await super().asyncSetUp()

        filepath = Path(getfile(self.__class__))
        self.dir: Path = filepath.parent

        self.project = self._init_project()
        self.processor: T = self._init_processor()

        awaitables = tuple(self.processor.process2(page) for page in self.project.pages)
        await gather(*awaitables)

    @abstractmethod
    def _init_project(self) -> Project:
        ...

    def _init_processor(self) -> T:
        return Processor()

    def subTest(self, msg: Any = ..., **params: Any):
        match msg:
            case Page() as page:
                return super().subTest(page.path_in_project.with_suffix(''))
            case _:
                return super().subTest(msg)

    def for_each_expected(self, suffix: str, *, subdir: str = '') -> Iterable[tuple[Page, Path]]:
        ok = True
        for page in self.project.pages:
            expected = self.dir / 'expected' / subdir / page.path_in_volume.with_suffix(suffix)
            if expected.exists():
                yield page, expected
            else:
                ok = False
                with self.subTest(page):
                    raise SkipTest
        if not ok:
            raise SkipTest

    def test_issues(self):
        for page in self.project.pages:
            with self.subTest(page):
                self.assertEqual([], self.processor.issues[page])
