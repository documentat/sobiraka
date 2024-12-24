from typing import Iterable, Sequence

from .fragment import Fragment


def clean_phrases(phrases: Sequence[Fragment], exceptions: Sequence[Sequence[Fragment]]) -> Iterable[str]:
    """
    Generates a special representation of `phrases`, with all `exceptions` removed.
    This does not affect any elements' positions due to placing necessary amounts of spaces.
    """
    for phrase in phrases:
        result = phrase.text
        for exc in exceptions[phrase.start.line]:
            if phrase.start <= exc.start and exc.end <= phrase.end:
                start = exc.start.char - phrase.start.char
                end = exc.end.char - phrase.start.char
                result = result[:start] + ' ' * len(exc.text) + result[end:]
        yield result
