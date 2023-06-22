import os
import re
from asyncio import create_subprocess_exec
from subprocess import PIPE
from typing import AsyncIterable, Sequence

from sobiraka.models import Volume
from sobiraka.runtime import RT


async def run_hunspell(words: Sequence[str], volume: Volume) -> AsyncIterable[str]:
    if not words:
        return

    environ = os.environ
    if volume.config.lint.dictionaries:
        environ = environ.copy()
        environ['DICPATH'] = ':'.join((
            str(RT.FILES / 'dictionaries'),
            str(volume.project.base)))
        environ['DICTIONARY'] = ','.join(volume.config.lint.dictionaries)

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

        if m := re.fullmatch(r'& (\S+) (\d+) (\d+): (.+)', line):
            misspelled_word, _, _, _ = m.groups()
            yield misspelled_word

        elif m := re.fullmatch(r'# (\S+) (\d+)', line):
            misspelled_word, _ = m.groups()
            yield misspelled_word

        elif m := re.fullmatch(r'\+ (\w+)', line):
            continue

        elif line in ('', '*', '-'):
            continue

        else:
            raise ValueError(line)
