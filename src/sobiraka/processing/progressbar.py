import sys
from asyncio import create_task, sleep

from colorama import Back, Fore, Style
from colorama.ansi import clear_line

from sobiraka.models import Page, PageStatus
from sobiraka.runtime import RT
from .abstract import Processor

ICONS = {
    PageStatus.INITIALIZE: f'{Fore.LIGHTMAGENTA_EX}┄',
    PageStatus.PREPARE: f'{Fore.LIGHTMAGENTA_EX}┄',
    PageStatus.PROCESS1: f'{Fore.LIGHTGREEN_EX}─',
    PageStatus.PROCESS2: f'{Fore.LIGHTGREEN_EX}━',
    PageStatus.PROCESS3: f'{Fore.LIGHTCYAN_EX}━',
    PageStatus.PROCESS4: f'{Fore.GREEN}━',

    PageStatus.FAILURE: f'{Back.LIGHTRED_EX}{Fore.WHITE}X',
    PageStatus.DEP_FAILURE: f'{Back.LIGHTYELLOW_EX}{Fore.BLACK}!',
    PageStatus.VOL_FAILURE: f'{Fore.LIGHTGREEN_EX}━',  # identical to PROCESS2
}

COLORS = {
    PageStatus.FAILURE: Fore.RED,
    PageStatus.DEP_FAILURE: Fore.LIGHTYELLOW_EX,
}


async def run_with_progressbar(processor: Processor):
    """
    Call `processor.run()` and display a nice progressbar until it finishes running.
    Then, display a nice list of issues that occurred, see `print_issues()`.
    """

    # Start processing
    running = create_task(processor.run())

    try:
        while True:
            # Clear whatever we wrote on the previous iteration
            print(clear_line(), end='\r', file=sys.stderr)

            # Print a one-character 'icon' representing each page's status
            for page in processor.get_pages():
                print(ICONS[RT[page].status], end=Style.RESET_ALL, file=sys.stderr)

            # Print a message, if the processor provides it
            if processor.message is not None:
                print(' ' + Fore.LIGHTBLACK_EX + processor.message, end=Style.RESET_ALL, file=sys.stderr)

            # Once the processing stopped, stop showing the progressbar.
            # Note that this is done after we have reacted to the latest status updates:
            # in the best case scenario, we have just finished painting it completely green,
            # which it probably was not one iteration earlier.
            if running.done():
                break

            # Take a small pause before the next iteration
            await sleep(0.01)

    finally:
        # Reset to default colors
        print(Back.RESET + Fore.RESET, file=sys.stderr)

    try:
        # At this point, we already know for sure that the processing has finished.
        # Thus, we can print the final list of issues for the user.
        if print_issues(processor):
            return 1

    finally:
        # Await for the task, so that Python prints any unexpected Exceptions that happened
        await running

    return 0


def print_issues(processor: Processor) -> bool:
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
