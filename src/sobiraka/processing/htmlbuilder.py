import os.path
import re
from asyncio import Task, create_subprocess_exec, create_task, gather, to_thread
from functools import partial
from os.path import relpath
from pathlib import Path
from shutil import copyfile
from subprocess import PIPE

import jinja2
from aiofiles.os import makedirs
from panflute import Element, Header, Image

from sobiraka.models import EmptyPage, Page, PageHref, Project, Volume
from sobiraka.utils import panflute_to_bytes
from .abstract import Processor


class HtmlBuilder(Processor):
    def __init__(self, project: Project):
        super().__init__()
        self.project: Project = project
        self._additional_files: set[Path] = set()
        self._jinja_environments: dict[Volume, jinja2.Environment] = {}

    async def run(self, output: Path):
        output.mkdir(parents=True, exist_ok=True)

        generating: list[Task] = []
        for page in self.project.pages:
            target_file = output / self.make_target_path(page)
            generating.append(create_task(self.generate_html_for_page(page, target_file)))

        await gather(*generating)

    async def generate_html_for_page(self, page: Page, target_file: Path):
        await self.process2(page)

        target_file.parent.mkdir(parents=True, exist_ok=True)

        pandoc = await create_subprocess_exec(
            'pandoc',
            '--from', 'json',
            '--to', 'html',
            '--wrap', 'none',
            stdin=PIPE,
            stdout=PIPE)
        html, _ = await pandoc.communicate(panflute_to_bytes(self.doc[page]))
        pandoc.stdin.close()
        await pandoc.wait()
        assert pandoc.returncode == 0

        template = await self.get_template(page.volume)
        html = await template.render_async(
            project=page.volume.project,
            volume=page.volume,
            page=page,
            title=self.titles[page],
            body=html.decode('utf-8').strip())

        target_file.write_text(html, encoding='utf-8')

    async def get_template(self, volume: Volume) -> jinja2.Template:
        try:
            jinja = self._jinja_environments[volume]
        except KeyError:
            jinja = self._jinja_environments[volume] = jinja2.Environment(
                loader=jinja2.FileSystemLoader(volume.html.theme),
                enable_async=True,
                comment_start_string='{{#',
                comment_end_string='#}}')
        return jinja.get_template('page.html')

    @classmethod
    def make_target_path(cls, page: Page) -> Path:
        target_path = Path()
        for part in page.path_in_volume.parts:
            target_path /= re.sub(r'^(\d+-)?', '', part)

        if isinstance(page, EmptyPage):
            target_path /= 'index.html'
        elif page.is_index():
            target_path = target_path.with_name('index.html')
        else:
            target_path = target_path.with_suffix('.html')

        prefix = page.volume.html.prefix or '$AUTOPREFIX'
        prefix = re.sub(r'\$\w+', partial(cls.replace_in_prefix, page), prefix)
        prefix = os.path.join(*prefix.split('/'))

        target_path = prefix / target_path
        return target_path

    @classmethod
    def replace_in_prefix(cls, page: Page, m: re.Match) -> str:
        return {
            '$LANG': page.volume.lang or '',
            '$VOLUME': page.volume.codename,
            '$AUTOPREFIX': page.volume.autoprefix,
        }[m.group()]

    def get_pages(self) -> tuple[Page, ...]:
        return self.project.pages

    def make_internal_url(self, href: PageHref, *, page: Page) -> str:
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
        path = elem.url.replace('$LANG', page.volume.lang or '')
        source_path = page.volume.paths.resources / path
        target_path = page.volume.html.resources_prefix / path
        if target_path not in self._additional_files:
            self._additional_files.add(target_path)
            await makedirs(target_path.parent, exist_ok=True)
            await create_task(to_thread(copyfile, source_path, target_path))
        elem.url = relpath(target_path, start=page.parent.path)
        return (elem,)
