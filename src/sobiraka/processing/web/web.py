from __future__ import annotations

import os.path
import re
from asyncio import to_thread
from datetime import datetime
from functools import lru_cache
from itertools import chain
from os.path import relpath
from shutil import copyfile, rmtree
from typing import final

import iso639
from panflute import Image
from typing_extensions import override

from sobiraka.models import DirPage, FileSystem, IndexPage, Page, PageHref, PageStatus, Project, Volume
from sobiraka.models.config import Config, Config_HighlightJS, Config_Prism, Config_Pygments, SearchIndexerName
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath, configured_jinja, convert_or_none
from .abstracthtml import AbstractHtmlBuilder, AbstractHtmlProcessor
from .head import HeadCssFile, HeadJsFile
from .highlight import HighlightJs, Highlighter, Prism, Pygments
from .search import PagefindIndexer, SearchIndexer
from ..abstract import ProjectBuilder, Theme
from ..load_processor import load_processor


@final
class WebBuilder(ProjectBuilder['WebProcessor', 'WebTheme'], AbstractHtmlBuilder):

    def __init__(self, project: Project, output: AbsolutePath, *, hide_index_html: bool = False):
        ProjectBuilder.__init__(self, project)
        AbstractHtmlBuilder.__init__(self)

        self.output: AbsolutePath = output
        self.hide_index_html: bool = hide_index_html

        self._indexers: dict[Volume, SearchIndexer] = {}

    def init_processor(self, volume: Volume) -> WebProcessor:
        fs: FileSystem = self.project.fs
        config: Config = volume.config
        processor_class = load_processor(
            convert_or_none(fs.resolve, config.web.processor),
            config.web.theme,
            WebProcessor)
        return processor_class(self)

    def init_theme(self, volume: Volume) -> WebTheme:
        return WebTheme(volume.config.web.theme)

    async def run(self):
        self.output.mkdir(parents=True, exist_ok=True)

        for volume in self.project.volumes:
            theme = self.themes[volume]

            # Launch page processing tasks
            for page in volume.pages:
                self.add_html_task(self.require(page, PageStatus.PROCESS4))

            # Launch non-page processing tasks
            self.add_html_task(self.add_directory_from_location(theme.static_dir, RelativePath('_static')))
            self.add_html_task(self.add_custom_files(volume))
            self.add_html_task(self.compile_theme_sass(theme, volume))
            self.add_html_task(self.prepare_search_indexer(volume))

        # Wait until all pages will be generated and all additional files will be copied to the output directory
        # This may include tasks that started as a side effect of generating the HTML pages
        await self.await_all_html_tasks()

        # Finalize all search indexers
        for indexer in self._indexers.values():
            await indexer.finalize()
            self._results |= indexer.results()

        self.delete_old_files()

    def delete_old_files(self):
        # Delete files that were not produced during this build
        all_files = set()
        all_dirs = set()
        for file in self.output.walk_all():
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

        await super().process4(page)
        await self.decorate_html(page)

        target_file = self.output / self.get_target_path(page)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_bytes(RT[page].bytes)
        self._results.add(target_file)

    async def decorate_html(self, page: Page):
        from ..toc import local_toc, toc

        volume = page.volume
        project = page.volume.project
        config = page.volume.config
        theme = self.themes[page.volume]

        root_prefix = self.get_root_prefix(page)
        head = self.heads[volume].render(root_prefix)

        html = await theme.page_template.render_async(
            builder=self,

            project=project,
            volume=volume,
            config=config,
            page=page,

            number=RT[page].number,
            title=RT[page].title,
            body=RT[page].bytes.decode('utf-8').strip(),

            head=head,
            now=datetime.now(),
            toc=lambda **kwargs: toc(volume.root_page,
                                     builder=self,
                                     toc_depth=volume.config.web.toc_depth,
                                     combined_toc=volume.config.web.combined_toc,
                                     current_page=page,
                                     **kwargs),
            local_toc=lambda: local_toc(page, builder=self, current_page=page),
            Language=iso639.Language,

            ROOT=root_prefix,
            ROOT_PAGE=self.make_internal_url(PageHref(volume.root_page), page=page),
            STATIC=self.get_path_to_static(page),
            RESOURCES=self.get_path_to_resources(page),
            theme_data=volume.config.web.theme_data,
        )

        RT[page].bytes = html.encode('utf-8')

    def get_target_path(self, page: Page) -> RelativePath:
        volume: Volume = page.volume
        config: Config = page.volume.config

        target_path = RelativePath()
        for part in page.path_in_volume.parts:
            target_path /= re.sub(r'^(\d+-)?', '', part)

        match page:
            case IndexPage():
                target_path = target_path.with_name('index.html')
            case DirPage():
                target_path /= 'index.html'
            case Page():
                if page.path_in_volume == RelativePath():
                    target_path = target_path.parent / 'index.html'
                else:
                    target_path = target_path.with_suffix('.html')
            case _:
                raise TypeError(page.__class__.__name__)

        prefix = config.web.prefix or '$AUTOPREFIX'
        prefix = self.expand_path_vars(prefix, volume)
        prefix = os.path.join(*prefix.split('/'))

        target_path = RelativePath(prefix) / target_path
        return target_path

    def get_relative_image_url(self, image: Image, page: Page) -> str:
        config: Config = page.volume.config
        image_path = RelativePath() / config.web.resources_prefix / image.url
        start_path = self.get_target_path(page).parent
        return relpath(image_path, start=start_path)

    def make_internal_url(self, href: PageHref, *, page: Page = None) -> str:
        if href.target is page:
            result = ''

        else:
            source_path = self.get_target_path(page) if page is not None else RelativePath()
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
        start = self.output / self.get_target_path(page)
        root_prefix = self.output.relative_to(start.parent)
        if root_prefix == RelativePath('.'):
            return ''
        return str(root_prefix) + '/'

    def get_path_to_static(self, page: Page) -> RelativePath:
        start = self.output / self.get_target_path(page)
        static = self.output / '_static'
        return static.relative_to(start.parent)

    def get_path_to_resources(self, page: Page) -> RelativePath:
        start = self.output / self.get_target_path(page)
        resources = self.output / page.volume.config.web.resources_prefix
        return resources.relative_to(start.parent)

    async def add_custom_files(self, volume: Volume):
        fs: FileSystem = self.project.fs
        config: Config = volume.config

        for script in config.web.custom_scripts:
            source = RelativePath(script)
            assert source.suffix == '.js'
            target = RelativePath() / 'js' / source.name
            await self.add_file_from_project(source, target)
            self.heads[volume].append(HeadJsFile(target))

        for style in config.web.custom_styles:
            source = RelativePath(style)
            match source.suffix:
                case '.css':
                    target = RelativePath() / 'css' / source.name
                    self.add_html_task(self.add_file_from_project(source, target))
                    self.heads[volume].append(HeadCssFile(target))

                case '.sass' | '.scss':
                    source = fs.resolve(source)
                    target = RelativePath('_static') / 'css' / f'{source.stem}.css'
                    self.add_html_task(to_thread(self.compile_sass, volume, source, target))
                    self.heads[volume].append(HeadCssFile(target))

                case _:
                    raise ValueError(source)

    async def prepare_search_indexer(self, volume: Volume):
        config: Config = volume.config
        if config.web.search.engine is None:
            return

        # Select the search indexer implementation
        indexer_class = {
            SearchIndexerName.PAGEFIND: PagefindIndexer,
        }[config.web.search.engine]

        # Select the index file path
        index_relative_path = None
        if config.web.search.index_path is not None:
            index_relative_path = self.expand_path_vars(config.web.search.index_path, volume)

        # Initialize the indexer
        indexer = indexer_class(self, volume, index_relative_path)
        await indexer.initialize()
        self._indexers[volume] = indexer

        # Put required files to the HTML head
        self.heads[volume] += indexer.head_tags()

    @override
    def add_file_from_data(self, target: RelativePath, data: str | bytes):
        target = self.output / target
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            target.write_text(data)
        else:
            target.write_bytes(data)
        self._results.add(target)

    @override
    async def add_file_from_location(self, source: AbsolutePath, target: RelativePath):
        target = self.output / target
        target.parent.mkdir(parents=True, exist_ok=True)
        await to_thread(copyfile, source, target)
        self._results.add(target)

    @override
    async def add_file_from_project(self, source: RelativePath, target: RelativePath):
        target = self.output / target
        await to_thread(self.project.fs.copy, source, target)
        self._results.add(target)

    @override
    def compile_sass(self, volume: Volume, source: AbsolutePath, target: RelativePath):
        css = self.compile_sass_impl(source)
        self.add_file_from_data(target, css)


class WebProcessor(AbstractHtmlProcessor[WebBuilder]):
    @override
    @lru_cache
    def get_highlighter(self, volume: Volume) -> Highlighter:
        config: Config = volume.config
        match config.web.highlight:
            case Config_HighlightJS() as config_highlightjs:
                return HighlightJs(config_highlightjs, self.builder)
            case Config_Prism() as config_prism:
                return Prism(config_prism, self.builder)
            case Config_Pygments() as config_pygments:
                return Pygments(config_pygments, self.builder)


@final
class WebTheme(Theme):
    def __init__(self, theme_dir: AbsolutePath):
        super().__init__(theme_dir)
        self.page_template = configured_jinja(theme_dir).get_template('web.html')
