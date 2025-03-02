import inspect
from abc import ABCMeta, abstractmethod
from asyncio import create_task
from traceback import format_exception
from typing import Any, Generic, Iterable, TypeVar
from unittest import SkipTest

from typing_extensions import override

from abstracttests.abstracttestwithrt import AbstractTestWithRtPages
from helpers import FakeBuilder, unfold_exception_types
from sobiraka.models import Page, PageStatus, Project
from sobiraka.processing.abstract import Builder
from sobiraka.utils import AbsolutePath, super_gather

T = TypeVar('T', bound=Builder)


class ProjectTestCase(AbstractTestWithRtPages, Generic[T], metaclass=ABCMeta):
    maxDiff = None

    REQUIRE: PageStatus = PageStatus.PROCESS2

    async def asyncSetUp(self):
        await super().asyncSetUp()

        self.project = self._init_project()
        self.builder: T = self._init_builder()

        await self._process()

    @abstractmethod
    def _init_project(self) -> Project:
        ...

    def _init_builder(self) -> T:
        return FakeBuilder(self.project)

    async def _process(self):
        tasks = []
        for page in self.project.pages:
            tasks.append(create_task(self.builder.waiter.wait(page, self.REQUIRE)))
        await super_gather(tasks)

    def subTest(self, msg: Any = ..., **params: Any):
        if isinstance(msg, Page):
            return super().subTest(msg.path_in_project.with_suffix(''), **params)
        if msg is ...:
            return super().subTest(**params)
        return super().subTest(msg, **params)

    def for_each_expected(self, suffix: str, *, subdir: str = '') -> Iterable[tuple[Page, AbsolutePath]]:
        test_dir = AbsolutePath(inspect.getfile(self.__class__)).parent
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


class FailingProjectTestCase(ProjectTestCase, metaclass=ABCMeta):
    EXPECTED_EXCEPTION_TYPES: set[type[BaseException]]

    @override
    async def _process(self):
        # pylint: disable=broad-exception-caught
        self.exceptions = ExceptionGroup('', [NoExceptionsWereRaisesDuringTheTest()])
        try:
            await super()._process()
        except* Exception as eg:
            self.exceptions = eg

    def test_exceptions(self):
        self.assertIsNotNone(self.exceptions)
        all_actual = unfold_exception_types(self.exceptions)

        if self.EXPECTED_EXCEPTION_TYPES != all_actual:
            self.assertEqual(self.EXPECTED_EXCEPTION_TYPES, all_actual,
                             ''.join(format_exception(self.exceptions)))


class NoExceptionsWereRaisesDuringTheTest(Exception):
    pass
