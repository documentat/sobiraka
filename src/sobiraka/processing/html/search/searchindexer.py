from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from panflute import CodeBlock, Image
from sobiraka.models import Page, Volume
from sobiraka.models.config import Config
from sobiraka.processing.abstract import Dispatcher

if TYPE_CHECKING:
    from sobiraka.processing import HtmlBuilder


class SearchIndexer(Dispatcher, metaclass=ABCMeta):

    def __init__(self, builder: 'HtmlBuilder', volume: Volume, index_path: Path):
        super().__init__()
        self.builder: HtmlBuilder = builder
        self.volume: Volume = volume
        self.index_path: Path = index_path

    @staticmethod
    def default_index_path(volume: Volume) -> Path:
        config: Config = volume.config
        return Path() / (config.html.search.index_path or '_pagefind')

    async def initialize(self):
        pass

    async def finalize(self):
        pass

    @abstractmethod
    def results(self) -> set[Path]:
        ...

    ################################################################################
    # Ignored elements

    async def process_code_block(self, code: CodeBlock, page: Page):
        return ()

    async def process_image(self, image: Image, page: Page):
        return ()
