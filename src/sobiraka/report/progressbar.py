import logging
import sys
from typing import TYPE_CHECKING

from colorama import Fore, Style
from colorama.ansi import clear_line

from sobiraka.runtime import RT
from .print_issues import print_issues
from .style import ICONS

if TYPE_CHECKING:
    from sobiraka.processing.abstract import Processor


async def run_with_progressbar(processor: 'Processor'):
    # Enable the progress bar and call `processor.run()`
    progressbar = ProgressBarLogHandler(processor)
    try:
        logging.getLogger().addHandler(progressbar)
        result = await processor.run()
        assert result in (0, None), result
        return 0

    # If any exception is raised, we send it to ProgressBarLogHandler which prints it.
    # Then, we print the list of issues that occurred during the processing.
    except:  # pylint: disable=bare-except
        logging.getLogger().exception(f'{processor.__class__.__name__} failed.')
        print_issues(processor)
        return 1

    finally:
        logging.getLogger().removeHandler(progressbar)


def update_progressbar(message: str = None):
    """
    Update the state of the progress bar. Call this function every time a PageStatus changes.
    Optionally, you can pass a `message` that will be shown next to the progress bar.
    """
    logging.getLogger().handle(ProgressBarUpdate(message))


class ProgressBarUpdate(logging.LogRecord):
    """
    Part of the implementation for update_progressbar().
    Should not be used directly.
    """
    def __init__(self, message: str = None):
        super().__init__('', logging.INFO, '', 0, message, None, None)

    def __repr__(self):
        if self.msg is not None:
            return f'{self.__class__.__name__}({self.msg!r})'
        return f'{self.__class__.__name__}()'


class ProgressBarLogHandler(logging.StreamHandler):
    """
    The actual log handler that renders a nice progressbar based on what happens in the processor.
    """
    def __init__(self, processor: 'Processor'):
        super().__init__()

        self.processor: 'Processor' = processor
        self.message: str | None = None

    def handle(self, record: logging.LogRecord):
        # When someone called update_progressbar(), we get a ProgressBarUpdate.
        # We should update a status message from it (if any) and update the progress bar.
        if isinstance(record, ProgressBarUpdate):
            if record.msg is not None:
                self.message = record.getMessage()
            self.render()

        # When exception() is called on the logger, we get a record with exc_info.
        # First, we update the progress bar one final time.
        # Then, we call the normal printing of the exception.
        elif record.exc_info is not None:
            self.render()
            print(clear_line(), Style.RESET_ALL, end='\n\n', file=sys.stderr)
            super().handle(record)

        # When any other logging happens, we get a normal record.
        # We print its message in the current line, moving the progress bar to the new line.
        # This will look like a normal growing log, but with a constantly updating progress bar below.
        else:
            print(clear_line(), Style.RESET_ALL, end='\r', file=sys.stderr)
            super().handle(record)
            self.render()

    def render(self):
        # Clear whatever we wrote on the previous iteration
        print(clear_line(), end='\r', file=sys.stderr)

        # Print a one-character 'icon' representing each page's status
        for page in self.processor.get_pages():
            print(ICONS[RT[page].status], end=Style.RESET_ALL, file=sys.stderr)

        # Print a message, if provided
        if self.message is not None:
            print(' ' + Fore.LIGHTBLACK_EX + self.message, end=Style.RESET_ALL, file=sys.stderr)
