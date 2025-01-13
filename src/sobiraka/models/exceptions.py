from abc import ABCMeta
from typing import Sequence

from sobiraka.models import Page, Volume
from sobiraka.models.issues import Issue


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
        this_many_issues = str(len(issues)) + ' issue' + ('s' if len(issues) > 1 else '')
        message = f'{this_many_issues} occurred in {page.path_in_project}:'
        for issue in issues:
            message += f'\n  {issue}'
        super().__init__(message)


class DependencyFailed(Exception):
    def __init__(self, page: Page):
        super().__init__(f'A dependency failed for {page.path_in_project}')


class VolumeFailed(Ignorable):
    def __init__(self, volume: Volume):
        super().__init__(f'Some pages failed in {volume.codename!r}')
