from shutil import rmtree

from sobiraka.utils import AbsolutePath


def clean_directory(path: AbsolutePath):
    for subpath in path.iterdir():
        if subpath.is_dir():
            rmtree(subpath)
        else:
            subpath.unlink()
