from tempfile import TemporaryDirectory

from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeFileSystem
from sobiraka.models import Page, Project, Volume
from sobiraka.models.config import Config, Config_Web
from sobiraka.models.load import _load_web_highlight
from sobiraka.processing.web import Head, WebBuilder
from sobiraka.utils import AbsolutePath, RelativePath


class AbstractHighlightTest(ProjectTestCase[WebBuilder]):
    """
    Load a highlighter configuration, create a project, render a page.
    Check that the necessary HeadTag were added and the expected HTML code was rendered.
    """
    CONFIG: str | dict[str, dict]
    FILES: tuple[str, ...] = ()
    CONTENT: str = '```shell\necho 1\n```'
    EXPECTED_HEAD: Head
    EXPECTED_RENDER: str

    def _init_project(self) -> Project:
        fs = FakeFileSystem()
        for file in self.FILES:
            fs.pseudofiles[RelativePath(file)] = ''

        config = Config(
            web=Config_Web(
                highlight=_load_web_highlight(self.CONFIG),
            )
        )

        return Project(fs, {
            RelativePath(): Volume(config, {
                RelativePath(): Page(self.CONTENT),
            })
        })

    def _init_builder(self):
        output = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        return WebBuilder(self.project, AbsolutePath(output))

    def test_head(self):
        self.assertEqual(self.EXPECTED_HEAD, self.builder.head)

    async def test_render(self):
        page = self.project.get_volume().root_page
        actual = (await self.builder.render_html(page)).decode().strip()
        self.assertEqual(self.EXPECTED_RENDER, actual)
