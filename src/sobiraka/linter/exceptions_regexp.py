import re
from functools import cache

from sobiraka.models import Volume


@cache
def exceptions_regexp(volume: Volume) -> re.Pattern | None:
    """
    Prepare a regular expression that matches any exception.
    If the volume declares no exceptions, returns `None`.
    """
    regexp_parts: list[str] = []
    for exceptions_path in volume.config.lint.exceptions:
        lines = volume.project.fs.read_text(exceptions_path).splitlines()
        for line in lines:
            line = line.strip()
            if exceptions_path.suffix == '.regexp':
                regexp_parts.append(line)
            else:
                regexp_parts.append(r'\b' + re.escape(line) + r'\b')
    if regexp_parts:
        return re.compile('|'.join(regexp_parts))
    return None
