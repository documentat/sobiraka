import os
import re
from asyncio import create_subprocess_exec
from subprocess import PIPE
from typing import AsyncIterable, Sequence

from sobiraka.models import Book
from sobiraka.runtime import RT


async def run_hunspell(words: Sequence[str], book: Book) -> AsyncIterable[str]:
    if not words:
        return

    environ = os.environ
    if book.lint.dictionaries:
        environ = environ.copy()
        environ['DICPATH'] = ':'.join((
            str(RT.FILES / 'dictionaries'),
            str(book.paths.manifest_path.parent)))
        environ['DICTIONARY'] = ','.join(book.lint.dictionaries)

    hunspell = await create_subprocess_exec(
        'hunspell',
        env=environ,
        stdin=PIPE,
        stdout=PIPE)
    hunspell_version = await hunspell.stdout.readline()
    assert re.match(br'Hunspell 1\..+\n', hunspell_version), hunspell_version

    hunspell.stdin.write(' '.join(words).encode('utf-8'))
    hunspell.stdin.close()

    async for line in hunspell.stdout:
        line = line.decode('utf-8').rstrip('\n')

        if m := re.fullmatch('& (\S+) (\d+) (\d+): (.+)', line):
            misspelled_word, near_misses_count, position, near_misses = m.groups()
            yield misspelled_word

        elif m := re.fullmatch('# (\S+) (\d+)', line):
            misspelled_word, position = m.groups()
            yield misspelled_word

        elif m := re.fullmatch('\+ (\w+)', line):
            continue

        elif line in ('', '*', '-'):
            continue

        else:
            raise ValueError(line)