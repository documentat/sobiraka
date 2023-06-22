import os.path
import re
from asyncio import Task, create_subprocess_exec, create_task, gather, to_thread
from datetime import datetime
from functools import partial
from os.path import relpath
from pathlib import Path
from shutil import copyfile
from subprocess import PIPE

import jinja2
from aiofiles.os import makedirs
from panflute import Element, Header, Image

from sobiraka.models import DirPage, GlobalToc, IndexPage, LocalToc, Page, PageHref, Project, Syntax, Volume
from sobiraka.utils import panflute_to_bytes
from .abstract import ProjectProcessor
from ..runtime import RT


class HtmlBuilder(ProjectProcessor):
    def __init__(self, project: Project, output: Path):
        super().__init__(project)
        self.output: Path = output

        self._generating: list[Task] = []
        self._copying: dict[Path, Task] = {}

        self._jinja_environments: dict[Volume, jinja2.Environment] = {}

    async def run(self):
        self.output.mkdir(parents=True, exist_ok=True)

        # Copy the theme's static directory
        for volume in self.project.volumes:
            static = volume.html.theme / '_static'
            for source_path in static.rglob('**/*'):
                if source_path.is_file():
                    target_path = self.output / '_static' / source_path.relative_to(static)
                    self._copying[target_path] = create_task(self.copy_file(source_path, target_path))

        # Copy additional static files
        for volume in self.project.volumes:
            for filename in volume.html.resources_force_copy:
                source_path = self.project.base / volume.html.resources_prefix / filename
                target_path = self.output / volume.html.resources_prefix / filename
                self._copying[target_path] = create_task(self.copy_file(source_path, target_path))

        # Generate the HTML pages in no particular order
        for page in self.project.pages:
            self._generating.append(create_task(self.generate_html_for_page(page)))
        await gather(*self._generating)

        # Wait until all additional files will be copied to the output directory
        # This may include tasks that started as a side effect of generating the HTML pages
        await gather(*self._copying.values())

    @staticmethod
    async def copy_file(source_path: Path, target_path: Path):
        await makedirs(target_path.parent, exist_ok=True)
        await to_thread(copyfile, source_path, target_path)

    async def generate_html_for_page(self, page: Page) -> str:
        volume = page.volume
        project = page.volume.project

        await self.process2(page)

        target_file = self.make_target_path(page)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        path_to_root_page = Path(relpath(self.make_target_path(volume.root_page), start=target_file.parent))
        path_to_static = Path(relpath(self.output / '_static', start=target_file.parent))
        path_to_resources = Path(relpath(self.output / volume.html.resources_prefix, start=target_file.parent))

        pandoc = await create_subprocess_exec(
            'pandoc',
            '--from', 'json',
            '--to', 'html',
            '--wrap', 'none',
            stdin=PIPE,
            stdout=PIPE)
        html, _ = await pandoc.communicate(panflute_to_bytes(self.doc[page]))
        assert pandoc.returncode == 0

        template = await self.get_template(page.volume)
        html = await template.render_async(
            builder=self,

            project=project,
            volume=volume,
            page=page,

            title=self.titles[page],
            body=html.decode('utf-8').strip(),

            now=datetime.now(),
            toc=GlobalToc_HTML(self, volume, page),
            local_toc=LocalToc(self, page),

            ROOT_PAGE=path_to_root_page,
            STATIC=path_to_static,
            RESOURCES=path_to_resources,
            theme_data=volume.html.theme_data,
        )

        target_file.write_text(html, encoding='utf-8')
        return html

    async def get_template(self, volume: Volume) -> jinja2.Template:
        try:
            jinja = self._jinja_environments[volume]
        except KeyError:
            jinja = self._jinja_environments[volume] = jinja2.Environment(
                loader=jinja2.FileSystemLoader((RT.FILES / 'themes' / volume.html.theme)),
                enable_async=True,
                undefined=jinja2.StrictUndefined,
                comment_start_string='{{#',
                comment_end_string='#}}')
        return jinja.get_template('page.html')

    def make_target_path(self, page: Page) -> Path:
        target_path = Path()
        for part in page.path_in_volume.parts:
            target_path /= re.sub(r'^(\d+-)?', '', part)

        match page:
            case IndexPage():
                target_path = target_path.with_name('index.html')
            case DirPage():
                target_path /= 'index.html'
            case Page():
                target_path = target_path.with_suffix('.html')
            case _:
                raise TypeError(page.__class__.__name__)

        prefix = page.volume.config.html.prefix or '$AUTOPREFIX'
        prefix = re.sub(r'\$\w+', partial(self.replace_in_prefix, page), prefix)
        prefix = os.path.join(*prefix.split('/'))

        target_path = self.output / prefix / target_path
        return target_path

    @classmethod
    def replace_in_prefix(cls, page: Page, m: re.Match) -> str:
        return {
            '$LANG': page.volume.lang or '',
            '$VOLUME': page.volume.codename,
            '$AUTOPREFIX': page.volume.autoprefix,
        }[m.group()]

    def make_internal_url(self, href: PageHref | Page, *, page: Page) -> str:
        if isinstance(href, Page):
            href = PageHref(href)

        if href.target is page:
            result = ''
        else:
            source_path = self.make_target_path(page)
            target_path = self.make_target_path(href.target)
            result = relpath(target_path, start=source_path.parent)

        if href.anchor:
            result += '#' + href.anchor

        return result

    async def process_header(self, elem: Header, page: Page) -> tuple[Element, ...]:
        elems = await super().process_header(elem, page)
        if elem.level == 1:
            return ()
        return elems

    async def process_image(self, elem: Image, page: Page) -> tuple[Image, ...]:
        path = Path(elem.url.replace('$LANG', page.volume.lang or ''))

        if path.is_absolute():
            source_path = page.volume.paths.resources / path.relative_to('/')
        else:
            source_path = (page.path.parent / path).resolve()

        target_path = self.output \
                      / page.volume.html.resources_prefix \
                      / source_path.relative_to(page.volume.paths.resources)

        if target_path not in self._copying:
            self._copying[target_path] = create_task(self.copy_file(source_path, target_path))
        elem.url = relpath(target_path, start=self.make_target_path(page).parent)
        return (elem,)


class GlobalToc_HTML(GlobalToc):
    processor: HtmlBuilder

    def get_href(self, page: Page) -> str:
        # TODO: implement something like make_target_path() in every Processor
        # pylint: disable=no-member
        current_path = self.processor.make_target_path(self.current)
        target_path = self.processor.make_target_path(page)
        return relpath(target_path, start=current_path.parent)

    def syntax(self) -> Syntax:
        return Syntax.HTML
