import re
from itertools import chain
from typing import Sequence

from more_itertools import first, last

from sobiraka.models.issues import IllegalApostrophe, IllegalQuotationMarks, Issue, MismatchingQuotationMarks, \
    UnclosedQuotationSpan, UnexpectedClosingQuotationMark
from sobiraka.utils import Apostrophe, QuotationMark


class QuotationsAnalyzer:
    def __init__(self, lines: Sequence[str],
                 allowed_quotation_marks: Sequence[Sequence[QuotationMark]] = (),
                 allowed_apostrophes: Sequence[Apostrophe] = ()):
        self.lines = tuple(lines)
        self.issues: list[Issue] = []

        self.allowed_quotation_marks = allowed_quotation_marks
        self.allowed_apostrophes = allowed_apostrophes
        for apostrophe in allowed_apostrophes:
            for incompatible_quotation_mark in apostrophe.incompatible_quotation_marks:
                if incompatible_quotation_mark in allowed_quotation_marks:
                    raise ValueError('Incompatible quotation marks and apostrophes.')

        for line in self.lines:
            self.issues += self.analyze_line(line)

    def analyze_line(self, line: str) -> Sequence[Issue]:
        # pylint: disable=too-many-branches

        issues: list[tuple[int, Issue]] = []
        openings: dict[QuotationMark, int] = {}

        # Search for all kind of quotation marks, both opening and closing
        for m in re.finditer(QuotationMark.regexp(), line):
            mark = m.group()
            is_potential_apo = any(mark == x.value for x in Apostrophe)
            is_allowed_qm = any(mark in x.value for x in chain(*self.allowed_quotation_marks))
            is_allowed_apo = any(mark == x.value for x in self.allowed_apostrophes)
            assert not (is_allowed_qm and is_allowed_apo)

            if openings and last(openings).closing == mark:
                # This closing is exactly what we expected after a recent opening
                # This means that it's time to report if the opening quotation mark was illegal
                # We didn't do it earlier because we want a beautiful message with the whole quotation
                if self.allowed_quotation_marks:
                    nesting = tuple(openings.keys())
                    for allowed_nesting in self.allowed_quotation_marks:
                        if allowed_nesting[:len(nesting)] == nesting:
                            break
                    else:
                        start = last(openings.values())
                        end = m.end()
                        issues.append((m.start(), IllegalQuotationMarks(nesting, line[start:end])))

                # And now forget about this quotation
                openings.popitem()

            elif is_potential_apo:
                # This looks like an apostrophe, and this is probably not a closing quotation mark
                # Treat is an apostrophe, regardless if it is allowed or not
                if is_allowed_apo:
                    continue

                if not is_allowed_qm:
                    word = first(w.group()
                                 for w in re.finditer(r"[\w'’]+", line)
                                 if w.start() <= m.start() <= w.end())
                    issues.append((m.start(), IllegalApostrophe(Apostrophe(mark), word)))

            elif self.is_opening(m):
                # This is an opening quotation mark
                # Treat is as an opening, regardless if it is allowed or not
                openings[QuotationMark.by_opening(mark)] = m.start()

            elif openings:
                # This is a closing quotation mark, but it does not match the opening
                # (if it did, another clause above would be executed insted)
                qm, start = openings.popitem()
                end = m.end()
                assert qm.closing != mark
                issues.append((start, MismatchingQuotationMarks(line[start:end])))

            else:
                # This is a closing quotation mark but there was no unclosed opening earlier
                issues.append((m.start(), UnexpectedClosingQuotationMark(line[:m.end()])))

        # Now that we reached the end of the line,
        # consider each unclosed opening mark an issue
        for start in openings.values():
            issues.append((start, UnclosedQuotationSpan(line[start:])))

        return tuple(y for x, y in sorted(issues))

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
