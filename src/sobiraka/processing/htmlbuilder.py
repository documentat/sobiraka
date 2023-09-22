from __future__ import annotations

import os.path
import re
from asyncio import Task, create_subprocess_exec, create_task, gather, to_thread
from datetime import datetime
from functools import partial
from itertools import chain
from os.path import relpath
from pathlib import Path
from shutil import copyfile, rmtree
from subprocess import PIPE

import iso639
from aiofiles.os import makedirs
from panflute import Element, Header, Image

from sobiraka.models import DirPage, GlobalToc, IndexPage, LocalToc, Page, PageHref, Project, Syntax, Volume
from sobiraka.utils import panflute_to_bytes
from .abstract import ProjectProcessor
from .plugin import HtmlTheme, load_html_theme


class HtmlBuilder(ProjectProcessor):
    def __init__(self, project: Project, output: Path, *, hide_index_html: bool = False):
        super().__init__(project)
        self.output: Path = output
        self.hide_index_html: bool = hide_index_html

        self._additional_tasks: list[Task] = []
        self._results: set[Path] = set()

        self._themes: dict[Volume, HtmlTheme] = {}
        for volume in project.volumes:
            self._themes[volume] = load_html_theme(volume.config.html.theme)

    async def run(self):
        self.output.mkdir(parents=True, exist_ok=True)

        # Copy the theme's static directory
        for volume in self.project.volumes:
            theme = self._themes[volume]
            for source_path in theme.static_dir.rglob('**/*'):
                if source_path.is_file():
                    target_path = self.output / '_static' / source_path.relative_to(theme.static_dir)
                    self._additional_tasks.append(create_task(self.copy_file_from_theme(source_path, target_path)))

        # Copy additional static files
        for volume in self.project.volumes:
            for filename in volume.config.html.resources_force_copy:
                source_path = (volume.config.paths.resources or volume.config.paths.root) / filename
                target_path = self.output / volume.config.html.resources_prefix / filename
                self._additional_tasks.append(create_task(self.copy_file_from_project(source_path, target_path)))

        # Generate the HTML pages in no particular order
        generating: list[Task] = []
        for page in self.project.pages:
            generating.append(create_task(self.generate_html_for_page(page)))
        await gather(*generating)

        # Wait until all additional files will be copied to the output directory
        # This may include tasks that started as a side effect of generating the HTML pages
        await gather(*self._additional_tasks)

        # Delete files that were not produced during this build
        all_files = set()
        all_dirs = set()
        for file in self.output.rglob('**/*'):
            if file.is_dir():
                all_dirs.add(file)
            else:
                all_files.add(file)
        files_to_delete = all_files - self._results
        dirs_to_delete = all_dirs - set(chain(*(f.parents for f in self._results)))
        for file in files_to_delete:
            file.unlink()
        for directory in dirs_to_delete:
            rmtree(directory, ignore_errors=True)

    async def copy_file_from_theme(self, source: Path, target: Path):
        await makedirs(target.parent, exist_ok=True)
        await to_thread(copyfile, source, target)
        self._results.add(target)

    async def copy_file_from_project(self, source: Path, target: Path):
        await makedirs(target.parent, exist_ok=True)
        await to_thread(self.project.fs.copy, source, target)
        self._results.add(target)

    async def generate_html_for_page(self, page: Page) -> str:
        volume = page.volume
        project = page.volume.project

        await self.process2(page)

        theme = self._themes[volume]
        if theme.__class__ is not HtmlTheme:
            await theme.process_container(self.doc[page], page)

        pandoc = await create_subprocess_exec(
            'pandoc',
            '--from', 'json',
            '--to', 'html',
            '--wrap', 'none',
            '--no-highlight',
            stdin=PIPE,
            stdout=PIPE)
        html, _ = await pandoc.communicate(panflute_to_bytes(self.doc[page]))
        assert pandoc.returncode == 0

        html = await theme.page_template.render_async(
            builder=self,

            project=project,
            volume=volume,
            page=page,

            title=self.titles.get(page, 'Untitled'),  # TODO why is title not there?
            body=html.decode('utf-8').strip(),

            now=datetime.now(),
            toc=GlobalToc_HTML(self, volume, page, volume.config.html.combined_toc),
            local_toc=LocalToc(self, page),
            Language=iso639.Language,

            ROOT=self.get_path_to_root(page),
            ROOT_PAGE=self.make_internal_url(volume.root_page, page=page),
            STATIC=self.get_path_to_static(page),
            RESOURCES=self.get_path_to_resources(page),
            theme_data=volume.config.html.theme_data,
        )

        target_file = self.get_target_path(page)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(html, encoding='utf-8')
        self._results.add(target_file)
        return html

    def get_target_path(self, page: Page) -> Path:
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
            source_path = self.get_target_path(page)
            target_path = self.get_target_path(href.target)
            if self.hide_index_html and target_path.name == 'index.html':
                target_path = target_path.parent
            result = relpath(target_path, start=source_path.parent)

        if href.anchor:
            result += '#' + href.anchor

        return result

    def get_path_to_root(self, page: Page) -> Path:
        start = self.get_target_path(page)
        return Path(relpath(self.output, start=start.parent))

    def get_path_to_static(self, page: Page) -> Path:
        start = self.get_target_path(page)
        static = self.output / '_static'
        return Path(relpath(static, start=start.parent))

    def get_path_to_resources(self, page: Page) -> Path:
        start = self.get_target_path(page)
        resources = self.output / page.volume.config.html.resources_prefix
        return Path(relpath(resources, start=start.parent))

    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        elems = await super().process_header(header, page)
        if header.level == 1:
            return ()
        return elems

    async def process_image(self, image: Image, page: Page) -> tuple[Image, ...]:
        config = page.volume.config

        # Run the default path processing
        image, = await super().process_image(image, page)
        assert isinstance(image, Image)

        # Schedule copying the image file to the output directory
        source_path = config.paths.resources / image.url
        target_path = self.output / config.html.resources_prefix / image.url
        if target_path not in self._additional_tasks:
            self._additional_tasks.append(create_task(self.copy_file_from_project(source_path, target_path)))

        # Use the path relative to the page path
        image.url = relpath(target_path, start=self.get_target_path(page).parent)
        return (image,)


class GlobalToc_HTML(GlobalToc):
    processor: HtmlBuilder

    def get_href(self, page: Page) -> str:
        return str(self.processor.make_internal_url(page, page=self.current))

    def syntax(self) -> Syntax:
        return Syntax.HTML
