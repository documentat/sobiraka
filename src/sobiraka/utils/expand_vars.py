import re

from .autoprefix import autoprefix


def expand_vars(text: str, *, lang: str, codename: str) -> str:
    def _substitution(m: re.Match) -> str:
        return {
            '$LANG': lang or '',
            '$VOLUME': codename or 'all',
            '$AUTOPREFIX': autoprefix(lang, codename),
        }[m.group()]

    return re.sub(r'\$\w+', _substitution, text)
