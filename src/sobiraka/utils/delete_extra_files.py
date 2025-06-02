from itertools import chain
from shutil import rmtree

from sobiraka.utils import AbsolutePath


def delete_extra_files(base_directory: AbsolutePath, expected_files: set[AbsolutePath]):
    all_files = set()
    all_dirs = set()
    for file in base_directory.walk_all():
        if file.is_dir():
            all_dirs.add(file)
        else:
            all_files.add(file)
    files_to_delete = all_files - expected_files
    dirs_to_delete = all_dirs - set(chain(*(f.parents for f in expected_files)))
    for file in files_to_delete:
        file.unlink()
    for directory in dirs_to_delete:
        rmtree(directory, ignore_errors=True)
