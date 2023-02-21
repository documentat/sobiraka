import re
from functools import cache

from sobiraka.models import Book


@cache
def exceptions_regexp(book: Book) -> re.Pattern | None:
    """
    Prepare a regular expression that matches any exception.
    If the book declares no exceptions, returns `None`.
    """
    regexp_parts: list[str] = []
    for exceptions_path in book.lint.exceptions:
        with exceptions_path.open() as exceptions_file:
            for line in exceptions_file:
                line = line.strip()
                if exceptions_path.suffix == '.regexp':
                    regexp_parts.append(line)
                else:
                    regexp_parts.append(r'\b' + re.escape(line) + r'\b')
    if regexp_parts:
        return re.compile('|'.join(regexp_parts))