from abc import ABCMeta

from sobiraka.utils import AbsolutePath


class Theme(metaclass=ABCMeta):
    def __init__(self, theme_dir: AbsolutePath):
        self.theme_dir = theme_dir
        self.static_dir = theme_dir / '_static'
