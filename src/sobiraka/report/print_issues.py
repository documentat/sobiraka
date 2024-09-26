import sys
from typing import TYPE_CHECKING

from colorama import Style

from sobiraka.models import Page, PageStatus
from sobiraka.runtime import RT
from .style import COLORS, ICONS

if TYPE_CHECKING:
    from sobiraka.processing.abstract import Processor


def print_issues(processor: 'Processor') -> bool:
    """
    For each page with the FAILURE status, print a list of issues that occurred.
    For each page with the DEP_FAILURE status, print a list of failed pages it depends on.
    Both lists are stylized using the same icons and colors as in the progressbar.
    """
    issues_count: int = 0
    failures: list[Page] = []
    dep_failures: list[Page] = []

    for page in processor.get_pages():
        if RT[page].status is PageStatus.FAILURE:
            issues_count += len(RT[page].issues)
            failures.append(page)
        elif RT[page].status is PageStatus.DEP_FAILURE:
            dep_failures.append(page)

    if len(failures) != 0:
        message = '\n' + ICONS[PageStatus.FAILURE] \
                  + Style.RESET_ALL + COLORS[PageStatus.FAILURE] + Style.BRIGHT + ' ' \
                  + 'Found ' + str(issues_count) + ' ' + ('issue' if issues_count == 1 else 'issues') \
                  + ' in ' + str(len(failures)) + ' ' + ('page' if len(failures) == 1 else 'pages') \
                  + ':' + Style.RESET_ALL
        for page in failures:
            message += '\n    ' + COLORS[PageStatus.FAILURE] + Style.BRIGHT + str(
                page.path_in_project) + Style.RESET_ALL
            for issue in RT[page].issues:
                message += '\n        ' + COLORS[PageStatus.FAILURE] + str(issue) + Style.RESET_ALL
        print(message, file=sys.stderr)

    if len(dep_failures) != 0:
        message = '\n' + ICONS[PageStatus.DEP_FAILURE] + Style.RESET_ALL + COLORS[PageStatus.DEP_FAILURE] + ' ' \
                  + 'The issues are blocking ' + str(len(dep_failures)) + ' more ' \
                  + ('page' if len(dep_failures) == 1 else 'pages') + ':'
        for page in dep_failures:
            message += '\n    ' + COLORS[PageStatus.DEP_FAILURE] + str(page.path_in_project) + Style.RESET_ALL
        print(message, file=sys.stderr)

    if len(failures) != 0 or len(dep_failures) != 0:
        print(file=sys.stderr)
        return True

    return False
