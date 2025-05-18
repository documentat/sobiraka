from dataclasses import dataclass, field

from rich.console import Console, ConsoleOptions, ConsoleRenderable, RenderResult
from rich.segment import Segment
from rich.text import Text
from rich.tree import Tree
from typing_extensions import override

from sobiraka.models import Page, Source
from sobiraka.report.style import make_report_icon, make_report_text


class TreeAndBlankLine(Tree):
    def __init__(self):
        super().__init__('', guide_style='red', hide_root=True)
        self.extra_new_line: bool = True

    @override
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield from super().__rich_console__(console, options)
        yield Segment.line()
        if self.extra_new_line:
            yield Segment.line()


@dataclass
class SourceWidget(ConsoleRenderable):
    source: Source
    page: Page = field(default=None)

    @property
    def obj(self) -> Page | Source:
        return self.page or self.source

    @override
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield make_report_icon(self.obj.status)
        yield Text(str(self.source.path_in_project.name), style='grey58', end='')

        if self.page:
            yield Text(' → ', style='grey58', end='')
            yield make_report_text(self.page.status, str(self.page.meta.permalink or self.page.location))

        if self.obj.exception is not None:
            yield Text('    ', end='')
            yield Text(self.obj.exception.__class__.__name__, style='red1 bold', end='')
            if str(self.obj):
                yield Text(f': {self.obj.exception}', style='red3')
        else:
            for issue in self.obj.issues:
                yield Text(f'    {issue}', style='red')
