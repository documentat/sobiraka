from __future__ import annotations

import os.path
import re
import sys
from asyncio import Task, TaskGroup, create_subprocess_exec, create_task, to_thread
from copy import deepcopy
from datetime import datetime
from itertools import chain
from os.path import relpath
from pathlib import Path
from shutil import copyfile, rmtree
from subprocess import PIPE

import iso639
from aiofiles.os import makedirs
from panflute import Element, Header, Image

from sobiraka.models import DirPage, FileSystem, IndexPage, Page, PageHref, PageStatus, Project, Volume
from sobiraka.models.config import Config, SearchIndexerName
from sobiraka.runtime import RT
from sobiraka.utils import panflute_to_bytes, super_gather

from .head import Head
from .search import PagefindIndexer, SearchIndexer
from ..abstract import ProjectProcessor
from ..plugin import HtmlTheme, load_html_theme


class HtmlBuilder(ProjectProcessor):
    def __init__(self, project: Project, output: Path, *, hide_index_html: bool = False):
        super().__init__(project)
        self.output: Path = output
        self.hide_index_html: bool = hide_index_html

        self._html_builder_tasks: list[Task] = []
        self._results: set[Path] = set()
        self._head: Head = Head()
        self._indexers: dict[Volume, SearchIndexer] = {}

        self._themes: dict[Volume, HtmlTheme] = {}
        for volume in project.volumes:
            self._themes[volume] = load_html_theme(volume.config.html.theme)

    async def run(self):
        self.output.mkdir(parents=True, exist_ok=True)

        for volume in self.project.volumes:
            config: Config = volume.config
            theme = self._themes[volume]

            # Launch page processing tasks
            for page in volume.pages:
                self._html_builder_tasks.append(create_task(self.require(page, PageStatus.PROCESS4)))

            # Launch non-page processing tasks
            self._html_builder_tasks += (
                create_task(self.copy_static_directory(theme)),
                create_task(self.copy_additional_static_files(volume)),
                create_task(self.compile_all_sass(theme)),
            )

            # Initialize search indexer
            if config.html.search.engine is not None:
                indexer = await self.prepare_search_indexer(volume)
                self._indexers[volume] = indexer
                self._head += indexer.head_tags()

        # Wait until all pages will be generated and all additional files will be copied to the output directory
        # This may include tasks that started as a side effect of generating the HTML pages
        await super_gather(self._html_builder_tasks, 'Some tasks failed when building HTML')

        # Finalize all search indexers
        for indexer in self._indexers.values():
            await indexer.finalize()
            self._results |= indexer.results()

        self.delete_old_files()

    async def copy_static_directory(self, theme: HtmlTheme):
        async with TaskGroup() as tg:
            for source_path in theme.static_dir.rglob('**/*'):
                if source_path.is_file():
                    target_path = self.output / '_static' / source_path.relative_to(theme.static_dir)
                    tg.create_task(self.copy_file_from_location(source_path, target_path))

    async def copy_additional_static_files(self, volume: Volume):
        async with TaskGroup() as tg:
            for filename in volume.config.html.resources_force_copy:
                source_path = (volume.config.paths.resources or volume.config.paths.root) / filename
                target_path = self.output / volume.config.html.resources_prefix / filename
                tg.create_task(self.copy_file_from_project(source_path, target_path))

    async def compile_all_sass(self, theme: HtmlTheme):
        fs: FileSystem = self.project.fs
        async with TaskGroup() as tg:
            for source_path, target_path in theme.sass_files.items():
                source_path = fs.resolve(theme.theme_dir / source_path)
                target_path = self.output / '_static' / target_path
                if target_path not in self._results:
                    tg.create_task(self.compile_sass(source_path, target_path))

    def delete_old_files(self):
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

    async def process4(self, page: Page):
        if indexer := self._indexers.get(page.volume):
            await indexer.add_page(page)

        theme = self._themes[page.volume]
        if theme.__class__ is not HtmlTheme:
            await theme.process_doc(RT[page].doc, page)

        self.apply_postponed_image_changes(page)

        await self.save_html(page, theme)

    def apply_postponed_image_changes(self, page: Page):
        for image, new_url in RT[page].converted_image_urls:
            image.url = new_url
        for image, link in RT[page].links_that_follow_images:
            link.url = image.url

    async def save_html(self, page: Page, theme: HtmlTheme):
        from ..toc import local_toc, toc

        volume = page.volume
        project = page.volume.project

        evil_copy = deepcopy(RT[page].doc)
        evil_copy.content.clear()

        pandoc = await create_subprocess_exec(
            'pandoc',
            '--from', 'json',
            '--to', 'html',
            '--wrap', 'none',
            '--no-highlight',
            stdin=PIPE,
            stdout=PIPE)
        html, _ = await pandoc.communicate(panflute_to_bytes(RT[page].doc))
        assert pandoc.returncode == 0

        root_prefix = str(self.get_root_prefix(page))
        head = self._head.render(root_prefix)

        html = await theme.page_template.render_async(
            builder=self,

            project=project,
            volume=volume,
            config=volume.config,
            page=page,

            number=RT[page].number,
            title=RT[page].title,
            body=html.decode('utf-8').strip(),

            head=head,
            now=datetime.now(),
            toc=lambda **kwargs: toc(volume.root_page,
                                     processor=self,
                                     toc_depth=volume.config.html.toc_depth,
                                     combined_toc=volume.config.html.combined_toc,
                                     current_page=page,
                                     **kwargs),
            local_toc=lambda: local_toc(page),
            Language=iso639.Language,

            ROOT=self.get_root_prefix(page),
            ROOT_PAGE=self.make_internal_url(volume.root_page, page=page),
            STATIC=self.get_path_to_static(page),
            RESOURCES=self.get_path_to_resources(page),
            theme_data=volume.config.html.theme_data,
        )

        target_file = self.get_target_path(page)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(html, encoding='utf-8')
        self._results.add(target_file)

    def get_target_path(self, page: Page) -> Path:
        volume: Volume = page.volume
        config: Config = page.volume.config

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

        prefix = config.html.prefix or '$AUTOPREFIX'
        prefix = self.expand_path_vars(prefix, volume)
        prefix = os.path.join(*prefix.split('/'))

        target_path = self.output / prefix / target_path
        return target_path

    @classmethod
    def expand_path_vars(cls, text: str, volume: Volume) -> str:
        def _substitution(m: re.Match) -> str:
            return {
                '$LANG': volume.lang or '',
                '$VOLUME': volume.codename or 'all',
                '$AUTOPREFIX': volume.autoprefix,
            }[m.group()]

        return re.sub(r'\$\w+', _substitution, text)

    def make_internal_url(self, href: PageHref | Page, *, page: Page) -> str:
        if isinstance(href, Page):
            href = PageHref(href)

        if href.target is page:
            result = ''

        else:
            source_path = self.get_target_path(page)
            target_path = self.get_target_path(href.target)
            add_slash = False

            if self.hide_index_html and target_path.name == 'index.html':
                target_path = target_path.parent
                add_slash = True

            result = relpath(target_path, start=source_path.parent)
            if add_slash:
                result += '/'

        if href.anchor:
            result += '#' + href.anchor

        return result

    def get_root_prefix(self, page: Page) -> str:
        start = self.get_target_path(page)
        root_prefix = relpath(self.output, start=start.parent)
        if root_prefix in ('', '.'):
            return ''
        return root_prefix + '/'

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
        config: Config = page.volume.config

        # Run the default processing
        # It is important to run it first, since it normalizes the path
        image, = await super().process_image(image, page)
        assert isinstance(image, Image)
        if image.url is None:
            return

        # Schedule copying the image file to the output directory
        source_path = config.paths.resources / image.url
        target_path = self.output / config.html.resources_prefix / image.url
        if target_path not in self._html_builder_tasks:
            self._html_builder_tasks.append(create_task(self.copy_file_from_project(source_path, target_path)))

        # Use the path relative to the page path
        # (we postpone the actual change in the element to not confuse the HtmlTheme custom code later)
        new_url = relpath(target_path, start=self.get_target_path(page).parent)
        RT[page].converted_image_urls.append((image, new_url))

        return (image,)

    async def prepare_search_indexer(self, volume: Volume) -> SearchIndexer:
        # Select the search indexer implementation
        config: Config = volume.config
        indexer_class = {
            SearchIndexerName.PAGEFIND: PagefindIndexer,
        }[config.html.search.engine]

        # Select the index file path
        if config.html.search.index_path is not None:
            index_path = self.output / self.expand_path_vars(config.html.search.index_path, volume)
        else:
            index_path = self.output / indexer_class.default_index_path(volume)

        # Initialize the indexer
        indexer = indexer_class(self, volume, index_path)
        await indexer.initialize()
        return indexer

    ################################################################################
    # Functions used for additional tasks

    async def copy_file_from_location(self, source: Path, target: Path):
        await makedirs(target.parent, exist_ok=True)
        await to_thread(copyfile, source, target)
        self._results.add(target)

    async def copy_file_from_project(self, source: Path, target: Path):
        await makedirs(target.parent, exist_ok=True)
        await to_thread(self.project.fs.copy, source, target)
        self._results.add(target)

    async def compile_sass(self, source: Path, destination: Path):
        await makedirs(destination.parent, exist_ok=True)

        sass = await create_subprocess_exec('sass', '--style=compressed', f'{source}:{destination}')
        await sass.wait()
        if sass.returncode != 0:
            print('SASS compilation failed.', file=sys.stderr)
            sys.exit(1)

        self._results.add(destination)
