from __future__ import annotations

import os.path
import re
from asyncio import Task, create_subprocess_exec, create_task, gather, to_thread
from datetime import datetime
from functools import partial
from itertools import chain
from os.path import normpath, relpath
from pathlib import Path
from shutil import rmtree
from subprocess import PIPE

import iso639
import jinja2
from aiofiles.os import makedirs
from panflute import Element, Header, Image

from sobiraka.models import DirPage, GlobalToc, IndexPage, LocalToc, Page, PageHref, Project, Syntax, Volume
from sobiraka.utils import panflute_to_bytes
from .abstract import ProjectProcessor


class HtmlBuilder(ProjectProcessor):
    def __init__(self, project: Project, output: Path):
        super().__init__(project)
        self.output: Path = output

        self._additional_tasks: list[Task] = []
        self._results: set[Path] = set()

        self._jinja_environments: dict[Volume, jinja2.Environment] = {}
        self._themes: dict[Volume, HtmlTheme] = {}

    async def run(self):
        self.output.mkdir(parents=True, exist_ok=True)

        # Copy the theme's static directory
        for volume in self.project.volumes:
            theme = self.get_theme(volume)
            for source_path in theme.static_dir.rglob('**/*'):
                if source_path.is_file():
                    target_path = self.output / '_static' / source_path.relative_to(theme.static_dir)
                    self._additional_tasks.append(create_task(self.copy_file(source_path, target_path)))

        # Copy additional static files
        for volume in self.project.volumes:
            for filename in volume.config.html.resources_force_copy:
                source_path = volume.config.html.resources_prefix / filename
                target_path = self.output / volume.config.html.resources_prefix / filename
                self._additional_tasks.append(create_task(self.project.fs.copy(source_path, target_path)))

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

    def get_theme(self, volume: Volume) -> HtmlTheme:
        if volume not in self._themes:
            self._themes[volume] = HtmlTheme(volume.config.html.theme)
        return self._themes[volume]

    async def copy_file(self, source: Path, target: Path):
        await makedirs(target.parent, exist_ok=True)
        await to_thread(self.project.fs.copy, source, target)
        self._results.add(target)

    async def generate_html_for_page(self, page: Page) -> str:
        volume = page.volume
        project = page.volume.project

        await self.process2(page)

        target_file = self.make_target_path(page)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        path_to_root_page = Path(relpath(self.make_target_path(volume.root_page), start=target_file.parent))
        path_to_static = Path(relpath(self.output / '_static', start=target_file.parent))
        path_to_resources = Path(relpath(self.output / volume.config.html.resources_prefix, start=target_file.parent))

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

        template = self.get_theme(volume).page_template
        html = await template.render_async(
            builder=self,

            project=project,
            volume=volume,
            page=page,

            title=self.titles.get(page, 'Untitled'),  # TODO why is title not there?
            body=html.decode('utf-8').strip(),

            now=datetime.now(),
            toc=GlobalToc_HTML(self, volume, page),
            local_toc=LocalToc(self, page),
            Language=iso639.Language,

            ROOT_PAGE=path_to_root_page,
            STATIC=path_to_static,
            RESOURCES=path_to_resources,
            theme_data=volume.config.html.theme_data,
        )

        target_file.write_text(html, encoding='utf-8')
        self._results.add(target_file)
        return html

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
            source_path = Path(normpath(page.path_in_project.parent / path))

        target_path = self.output \
                      / page.volume.config.html.resources_prefix \
                      / source_path.relative_to(page.volume.config.paths.resources)

        if target_path not in self._additional_tasks:
            self._additional_tasks.append(create_task(self.copy_file(source_path, target_path)))
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


class HtmlTheme:
    def __init__(self, path: Path):
        self.path: Path = path
        self.static_dir: Path = path / '_static'

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(path),
            enable_async=True,
            undefined=jinja2.StrictUndefined,
            comment_start_string='{{#',
            comment_end_string='#}}')

        self.page_template: jinja2.Template = env.get_template('page.html')
