from .sourcefile import SourceFile
from ..page import IndexPage


class IndexSourceFile(SourceFile):
    PAGE_CLASS = IndexPage
