from bisect import bisect_left, bisect_right
from typing import Iterable, Sequence

from panflute import Code, ListItem, stringify

from sobiraka.models.issues import Issue, PhraseBeginsWithLowerCase
from sobiraka.processing.txt import Fragment, TextModel


def phrases_must_begin_with_capitals(tm: TextModel, phrases: Sequence[Fragment]) -> Iterable[Issue]:
    for phrase in phrases:
        yield from _phrases_must_begin_with_capital(tm, phrase)


def _phrases_must_begin_with_capital(tm: TextModel, phrase: Fragment) -> Iterable[Issue]:
    if not phrase.text[0].islower():
        return

    for exception in tm.exceptions()[phrase.start.line]:
        if exception.start <= phrase.start < exception.end:
            return

    left = bisect_left(tm.fragments, phrase.start, key=lambda f: f.start)
    right = bisect_right(tm.fragments, phrase.start, key=lambda f: f.start)
    fragments_start_here = list(f for f in tm.fragments[left:right] if f.start == phrase.start)
    for fragment in fragments_start_here:
        match fragment.element:

            case Code():
                return

            case ListItem() as li:
                if stringify(li.parent.prev).rstrip().endswith(':'):
                    return

    yield PhraseBeginsWithLowerCase(phrase.text)
