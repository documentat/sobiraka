from pathlib import Path
from shutil import rmtree


def clean_directory(path: Path):
    for subpath in path.iterdir():
        if subpath.is_dir():
            rmtree(subpath)
        else:
            subpath.unlink()
