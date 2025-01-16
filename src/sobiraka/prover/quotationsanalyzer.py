import re
from typing import Iterable, Sequence

from sobiraka.models.issues import IllegalQuotationMarks, Issue, MismatchingQuotationMarks, UnclosedQuotationSpan
from sobiraka.utils import QuotationMark


class QuotationsAnalyzer:
    def __init__(self, lines: Sequence[str], allowed_quotation_marks: Sequence[Sequence[QuotationMark]] = None):
        self.lines = tuple(lines)
        self.allowed_quotation_marks = allowed_quotation_marks

        self.issues: list[Issue] = []

        for line in self.lines:
            self.issues += self.analyze_line(line)

    def analyze_line(self, line: str) -> Iterable[Issue]:
        openings: list[tuple[int, QuotationMark]] = []

        # Search for all kind of quotation marks, both opening and closing
        for m in re.finditer(QuotationMark.regexp(), line):
            mark = m.group()

            if self.is_opening(m):
                # Remember the opening position
                openings.append((m.start(), QuotationMark.by_opening(mark)))

                # Make sure that the current nesting is allowed
                if self.allowed_quotation_marks:
                    nesting = tuple(x[1] for x in openings)
                    for allowed_nesting in self.allowed_quotation_marks:
                        if allowed_nesting[:len(nesting)] == nesting:
                            break
                    else:
                        yield IllegalQuotationMarks(nesting, line[m.start():])

            else:
                start, qm = openings.pop()
                end = m.end()

                # Check if the latest opening mark matched this closing mark
                if qm.closing != mark:
                    yield MismatchingQuotationMarks(line[start:end])
                    continue

        # Now that we reached the end of the line,
        # consider each unclosed opening mark an issue
        for start, _ in openings:
            yield UnclosedQuotationSpan(line[start:])

    def is_opening(self, m: re.Match[str]) -> bool:
        """
        Guess if the author intended to open a new quotation span here.
        """
        # pylint: disable=too-many-return-statements
        match m.group():
            case '«':
                return True

            case '»':
                return False

            case _:
                is_start = m.start() == 0
                is_end = m.start() == len(m.string) - 1

                # Any quotation mark at the line start is obviously intended to be an opening
                # Any quotation mark at the line end is obviously intended to be a closing
                if is_start:
                    return True
                if is_end:
                    return False

                for p in reversed(m.string[:m.start()]):
                    if p in '"”»':
                        continue  # Probably there are multiple nested spans being closed
                    if p.isspace():
                        return True  # A quotation mark after a space. Definitely an opening
                    if p.isalnum():
                        return False  # A quotation mark after a word. Definitely a closing

                # When unsure, let's call it an opening
                return True
