from dataclasses import dataclass
from enum import Enum
from importlib.resources import files
from typing import Self

from sobiraka.models import FileSystem
from sobiraka.utils import AbsolutePath, RelativePath


def find_theme_dir(name: str, *, fs: FileSystem) -> AbsolutePath:
    theme_dir = RelativePath(name)

    if fs.exists(theme_dir) and fs.is_dir(theme_dir):
        return fs.resolve(theme_dir)

    if len(theme_dir.parts) == 1:
        theme_dir = AbsolutePath(files('sobiraka')) / 'files' / 'themes' / theme_dir
        if theme_dir.exists() and theme_dir.is_dir():
            return theme_dir

    raise FileNotFoundError(name)


@dataclass(kw_only=True, frozen=True)
class Config_Theme:
    path: AbsolutePath
    flavor: str = None
    customization: RelativePath = None

    @classmethod
    def from_name(cls, name: str) -> Self:
        return Config_Theme(path=AbsolutePath(files('sobiraka')) / 'files' / 'themes' / name)


class CombinedToc(Enum):
    NEVER = 'never'
    CURRENT = 'current'
    ALWAYS = 'always'

    @classmethod
    def from_bool(cls, value: bool) -> Self:
        if value:
            return CombinedToc.ALWAYS
        return CombinedToc.NEVER
