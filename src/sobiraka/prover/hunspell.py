import os
import re
from asyncio import create_subprocess_exec
from contextlib import contextmanager
from importlib.resources import files
from subprocess import PIPE
from tempfile import TemporaryDirectory
from typing import Generator, Sequence

from sobiraka.models import FileSystem, RealFileSystem, Volume
from sobiraka.utils import AbsolutePath, RelativePath


@contextmanager
def _prepare_hunspell_environ(fs: FileSystem, dictionaries: list[str]) -> Generator[dict[str, str], None, None]:
    """
    If necessary, create a temporary directory and copy all dictionaries there.
    If not necessary, don't do it.
    In any case, update the DICPATH and DICTIONARY environment variables.

    Return a dictionary that can be used as the environment when running Hunspell.
    """
    default_dictionaries_path = AbsolutePath(files('sobiraka')) / 'files' / 'dictionaries'

    # Collect all used DIC and AFF files from the project
    # Note that the AFF files are optional, while the DIC files are mandatory
    used_files_from_project: list[RelativePath] = []
    for dictionary in dictionaries:
        # If it is a DIC file, it potentially represents a pair of DIC and AFF files
        if dictionary.endswith('.dic'):
            dic_relpath = RelativePath(dictionary)
            aff_relpath = RelativePath(dictionary).with_suffix('.aff')
            if fs.exists(dic_relpath):
                used_files_from_project.append(dic_relpath)
                if fs.exists(aff_relpath):
                    used_files_from_project.append(aff_relpath)

        # If it's not a project dictionary, it must be an existing default dictionary
        elif not (default_dictionaries_path / f'{dictionary}.dic').exists():
            raise FileNotFoundError(dictionary)

    # Start preparing the environment that will be used to run Hunspell
    environ = os.environ.copy()
    environ['DICPATH'] = str(default_dictionaries_path)
    environ['DICTIONARY'] = ','.join(re.sub(r'\.dic$', '', d) for d in dictionaries)

    if not used_files_from_project:
        # We don't need to add the path to project's dictionaries
        # because none of them were referenced
        yield environ

    elif isinstance(fs, RealFileSystem):
        # The project happens to use a RealFileSystem, so there is no need to copy anything
        # Just specify the RealFileSystem's base as one of the paths
        environ['DICPATH'] = str(fs.base) + ':' + environ['DICPATH']
        yield environ

    else:
        # The project uses some non-real type of FileSystem (most likely we are in a test)
        # Create a temporary directory and copy files into it
        with TemporaryDirectory(prefix='sobiraka-hunspell-') as tempdir:
            for file in used_files_from_project:
                fs.copy(file, AbsolutePath(tempdir) / file)
            environ['DICPATH'] = tempdir + ':' + environ['DICPATH']
            yield environ


async def run_hunspell(words: Sequence[str], volume: Volume) -> Sequence[str]:
    if not words:
        return ()

    with _prepare_hunspell_environ(volume.project.fs, volume.config.prover.dictionaries) as environ:
        hunspell = await create_subprocess_exec('hunspell', env=environ, stdin=PIPE, stdout=PIPE)

        # Verify the Hunspell version in the first line
        hunspell_version = await hunspell.stdout.readline()
        assert re.match(br'Hunspell 1\..+\n', hunspell_version), hunspell_version

        # Send all the words for Hunspell to analyze
        # Note that Hunspell may misinterpret something when the lines are too long,
        # that's why we separate words with newlines, not just spaces
        hunspell.stdin.write('\n'.join(words).encode('utf-8'))
        hunspell.stdin.close()

        misspelled_words: list[str] = []

        async for line in hunspell.stdout:
            line = line.decode('utf-8').rstrip('\n')

            if m := re.fullmatch(r'& (\S+) (\d+) (\d+): (.+)', line):
                misspelled_word, _, _, _ = m.groups()
                misspelled_words.append(misspelled_word)

            elif m := re.fullmatch(r'# (\S+) (\d+)', line):
                misspelled_word, _ = m.groups()
                misspelled_words.append(misspelled_word)

            elif m := re.fullmatch(r'\+ (\w+)', line):
                continue

            elif line in ('', '*', '-'):
                continue

            else:
                raise ValueError(line)

        return misspelled_words
