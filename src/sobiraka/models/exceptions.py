from abc import ABCMeta
from typing import Sequence

from sobiraka.models import Issue, Page, Volume


class Ignorable(Exception, metaclass=ABCMeta):
    """
    An exception that is not worth reporting.
    When caught in `super_gather()`, such an exception is not included in the ExceptionGroup.
    """


class DisableLink(Exception):
    pass


class IssuesOccurred(Exception):
    def __init__(self, page: Page, issues: Sequence[Issue]):
        self.page: Page = page
        self.issues: tuple[Issue, ...] = tuple(issues)

        assert len(issues) > 0
        message = str(len(issues)) + ' issue' + ('s' if len(issues) > 1 else '') \
            + ' occurred in ' + str(page.path_in_project)
        super().__init__(message)


class DependencyFailed(Exception):
    def __init__(self, page: Page):
        super().__init__(f'A dependency failed for {page.path_in_project}')


class VolumeFailed(Ignorable):
    def __init__(self, volume: Volume):
        super().__init__(f'Some pages failed in {volume.codename!r}')


class SomePagesFailed(ExceptionGroup):
    def __new__(cls, exceptions: list[Exception]):
        return super().__new__(cls, 'Some pages failed', exceptions)
