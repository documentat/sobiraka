from abc import ABCMeta, abstractmethod
from typing import Generic, Iterable, TYPE_CHECKING, TypeVar

from panflute import Block, CodeBlock

from sobiraka.models import FileSystem
from sobiraka.models.config import JavaScriptHighlighterLibraryConfig
from sobiraka.utils import RelativePath
from ..head import HeadCssFile, HeadCssUrl, HeadJsFile, HeadJsUrl, HeadTag

if TYPE_CHECKING:
    from sobiraka.processing.web import WebBuilder


class Highlighter(metaclass=ABCMeta):
    """
    Base class for all highlighting implementations.
    """

    @abstractmethod
    def highlight(self, block: CodeBlock) -> tuple[Block, Iterable[HeadTag]]:
        """
        Given a code block, return:

        - the block (e.g., a RawBlock) for displaying it on the page,
        - zero or more HeadTag entries (e.g., language support plugins) to add to the Head.
        """


JSHLC = TypeVar('JSHLC', bound=JavaScriptHighlighterLibraryConfig)


class JavaScriptHighlighterLibrary(Highlighter, Generic[JSHLC], metaclass=ABCMeta):
    """
    Base class for JavaScript-based implementations of Highlighter.
    Works with WebBuilder only.
    """

    @staticmethod
    @abstractmethod
    def get_core_scripts() -> Iterable[str]:
        """One or more subpaths to the JS files that must be loaded for the library to work."""

    @staticmethod
    @abstractmethod
    def get_style_subpath(style: str) -> str:
        """The subpath to the CSS file of the given highlighting style."""

    def __init__(self, config: JSHLC, builder: 'WebBuilder'):
        super().__init__()
        self.config: JSHLC = config
        self.builder: WebBuilder = builder
        self.head: list[HeadTag] = []

        # If the location is a path, check that the necessary files exist
        if isinstance(config.location, RelativePath):
            fs: FileSystem = builder.project.fs

            # Check that the JS files exist locally
            for core_script in self.get_core_scripts():
                script_path = config.location / core_script
                if not fs.exists(script_path):
                    raise FileNotFoundError(script_path)
                self.head.append(HeadJsFile(script_path))

            # If a style is defined, check that the CSS file exists locally
            # (if not, assume that the designer took care of the styles manually)
            if config.style is not None:
                style_path = config.location / self.get_style_subpath(config.style)
                if not fs.exists(style_path):
                    raise FileNotFoundError(style_path)
                self.head.append(HeadCssFile(style_path))

        # If the location is a URL, don't check anything, just create the tags
        else:
            for core_script in self.get_core_scripts():
                script_url = config.location + '/' + core_script
                self.head.append(HeadJsUrl(script_url))
            if config.style is not None:
                style_url = config.location + '/' + self.get_style_subpath(config.style)
                self.head.append(HeadCssUrl(style_url))


class LanguageCannotBeHighlighted(Exception):
    pass
