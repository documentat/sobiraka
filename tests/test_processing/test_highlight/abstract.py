from abc import ABCMeta
from tempfile import TemporaryDirectory

from typing_extensions import override

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from helpers.fakefilesystem import PseudoFiles
from sobiraka.models.config import Config, Config_Paths, Config_Web, Config_Web_Highlight
from sobiraka.processing.html import Head
from sobiraka.processing.web import WebBuilder
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
    def additional_files(self) -> PseudoFiles:
        return {file: '' for file in self.FILES}

    @override
    def _init_config(self) -> Config:
        return Config(
            paths=Config_Paths(root=RelativePath('src')),
            web=Config_Web(highlight=Config_Web_Highlight.load(self.CONFIG))
        )

    def _init_builder(self):
        # pylint: disable=consider-using-with
        output = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        return WebBuilder(self.project, AbsolutePath(output))

    def test_head(self):
        self.assertEqual(self.EXPECTED_HEAD, self.builder.heads[self.project.documents[0]])

    async def test_render(self):
        page, = self.project.get_document().root.all_pages()
        actual = (await self.builder.render_html(page)).decode().strip()
        self.assertEqual(self.EXPECTED_RENDER, actual)
