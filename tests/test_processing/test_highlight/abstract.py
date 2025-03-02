from abc import ABCMeta
from tempfile import TemporaryDirectory

from typing_extensions import override

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from helpers import FakeFileSystem
from sobiraka.models import FileSystem
from sobiraka.models.config import Config, Config_Web
from sobiraka.models.load.load_volume import _load_web_highlight
from sobiraka.processing.web import Head, WebBuilder
from sobiraka.utils import AbsolutePath, RelativePath


class AbstractHighlightTest(SinglePageProjectTest[WebBuilder], metaclass=ABCMeta):
    """
    Load a highlighter configuration, create a project, render a page.
    Check that the necessary HeadTag were added and the expected HTML code was rendered.
    """
    SOURCE = '```shell\necho 1\n```'

    CONFIG: str | dict[str, dict]
    FILES: tuple[str, ...] = ()
    EXPECTED_HEAD: Head
    EXPECTED_RENDER: str

    @override
    def _init_filesystem(self) -> FileSystem:
        fs = FakeFileSystem()
        for file in self.FILES:
            fs.pseudofiles[RelativePath(file)] = ''
        return fs

    @override
    def _init_config(self) -> Config:
        return Config(
            web=Config_Web(
                highlight=_load_web_highlight(self.CONFIG),
            )
        )

    def _init_builder(self):
        # pylint: disable=consider-using-with
        output = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        return WebBuilder(self.project, AbsolutePath(output))

    def test_head(self):
        self.assertEqual(self.EXPECTED_HEAD, self.builder.heads[self.project.volumes[0]])

    async def test_render(self):
        page = self.project.get_volume().root_page
        actual = (await self.builder.render_html(page)).decode().strip()
        self.assertEqual(self.EXPECTED_RENDER, actual)
