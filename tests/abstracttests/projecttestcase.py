import inspect
from abc import ABCMeta, abstractmethod
from asyncio import gather
from pathlib import Path
from typing import Any, Generic, Iterable, TypeVar
from unittest import IsolatedAsyncioTestCase, SkipTest

from sobiraka.models import Page, Project
from sobiraka.processing.abstract import Processor
from sobiraka.runtime import RT

T = TypeVar('T', bound=Processor)


class ProjectTestCase(IsolatedAsyncioTestCase, Generic[T], metaclass=ABCMeta):
    maxDiff = None

    async def asyncSetUp(self):
        await super().asyncSetUp()

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
        if isinstance(msg, Page):
            return super().subTest(msg.path_in_project.with_suffix(''), **params)
        elif msg is ...:
            return super().subTest(**params)
        else:
            return super().subTest(msg, **params)

    def for_each_expected(self, suffix: str, *, subdir: str = '') -> Iterable[tuple[Page, Path]]:
        test_dir = Path(inspect.getfile(self.__class__)).parent
        ok = True
        for page in self.project.pages:
            expected = test_dir / 'expected' / subdir / page.path_in_volume.with_suffix(suffix)
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
                self.assertEqual([], RT[page].issues)
