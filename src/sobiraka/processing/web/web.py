from __future__ import annotations

from asyncio import create_task, to_thread
from datetime import datetime
from functools import lru_cache
from os.path import relpath
from shutil import copyfile
from typing import final

import iso639
from panflute import Image
from typing_extensions import override

from sobiraka.models import Document, FileSystem, Page, PageHref, Project
from sobiraka.models.config import Config, Config_HighlightJS, Config_Prism, Config_Pygments, SearchIndexerName
from sobiraka.processing.html import AbstractHtmlBuilder, AbstractHtmlProcessor, AbstractHtmlTheme, HeadCssFile, \
    HeadJsFile
from sobiraka.processing.html.highlight import HighlightJs, Highlighter, Prism, Pygments
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath, convert_or_none, delete_extra_files, expand_vars
from .search import PagefindIndexer, SearchIndexer
from ..abstract import ThemeableProjectBuilder
from ..load_processor import load_processor


@final
class WebBuilder(ThemeableProjectBuilder['WebProcessor', 'WebTheme'], AbstractHtmlBuilder):

    def __init__(self, project: Project, output: AbsolutePath, *, hide_index_html: bool = False):
        ThemeableProjectBuilder.__init__(self, project)
        AbstractHtmlBuilder.__init__(self)

        self.output: AbsolutePath = output
        self.hide_index_html: bool = hide_index_html

        self._indexers: dict[Document, SearchIndexer] = {}

    def init_processor(self, document: Document) -> WebProcessor:
        fs: FileSystem = self.project.fs
        config: Config = document.config
        processor_class = load_processor(
            convert_or_none(fs.resolve, config.web.processor),
            config.web.theme.path,
            WebProcessor)
        return processor_class(self)

    def init_theme(self, document: Document) -> WebTheme:
        return WebTheme(document.config.web.theme)

    @override
    def additional_variables(self) -> dict:
        return dict(HTML=True, WEB=True)

    async def run(self):
        self.output.mkdir(parents=True, exist_ok=True)

        for document in self.get_documents():
            theme = self.themes[document]

            # Prepare non-page processing tasks
            self.waiter.add_task(self.add_directory_from_location(theme.static_dir, RelativePath('_static')))
            self.process3_tasks[document].append(create_task(self.add_custom_files(document)))
            self.process3_tasks[document].append(create_task(self.compile_theme_sass(theme, document)))
            self.process3_tasks[document].append(create_task(self.prepare_search_indexer(document)))

        # Wait until all pages will be generated and all additional files will be copied to the output directory
        # This may include tasks that started as a side effect of generating the HTML pages
        await self.waiter.wait_all()

        # Finalize all search indexers
        for indexer in self._indexers.values():
            await indexer.finalize()
            self._results |= indexer.results()

        delete_extra_files(self.output, self._results)

    @override
    async def do_process4(self, page: Page):
        if indexer := self._indexers.get(page.document):
            await indexer.add_page(page)

        await super().do_process4(page)
        await self.decorate_html(page)

        target_file = self.output / self.get_target_path(page)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_bytes(RT[page].bytes)
        self._results.add(target_file)

    async def decorate_html(self, page: Page):
        from ..toc import local_toc, toc

        document = page.document
        project = page.document.project
        config = page.document.config
        theme = self.themes[page.document]

        root_prefix = self.get_root_prefix(page)
        head = self.heads[document].render(root_prefix)

        html = await theme.page_template.render_async(
            builder=self,

            project=project,
            document=document,
            config=config,
            page=page,

            number=RT[page].number,
            title=page.meta.title,
            body=RT[page].bytes.decode('utf-8').strip(),

            head=head,
            now=datetime.now(),
            toc=lambda **kwargs: toc(document.root_page,
                                     builder=self,
                                     toc_depth=document.config.web.toc_depth,
                                     combined_toc=document.config.web.combined_toc,
                                     current_page=page,
                                     **kwargs),
            local_toc=lambda: local_toc(page, builder=self, current_page=page),
            Language=iso639.Language,

            ROOT=root_prefix,
            ROOT_PAGE=self.make_internal_url(PageHref(document.root_page), page=page),
            STATIC=self.get_path_to_static(page),
            RESOURCES=self.get_path_to_resources(page),
            theme_data=document.config.web.theme_data,
            **document.config.variables,
        )

        RT[page].bytes = html.encode('utf-8')

    def get_target_path(self, page: Page) -> RelativePath:
        document: Document = page.document
        config: Config = page.document.config

        prefix = config.web.prefix or '$AUTOPREFIX'
        prefix = expand_vars(prefix, lang=document.lang, codename=document.codename)

        page_location = page.meta.permalink or page.location
        target_path = RelativePath() / prefix / page_location.as_path()
        if page_location.is_dir:
            target_path /= 'index.html'
        else:
            target_path = target_path.with_name(target_path.name + '.html')

        return target_path

    def get_relative_image_url(self, image: Image, page: Page) -> str:
        config: Config = page.document.config
        image_path = RelativePath() / config.web.resources_prefix / image.url
        start_path = self.get_target_path(page).parent
        return relpath(image_path, start=start_path)

    def make_internal_url(self, href: PageHref, *, page: Page = None) -> str:
        source_location = page and (page.meta.permalink or page.location)
        target_location = href.target.meta.permalink or href.target.location

        result = target_location.as_relative_path_str(
            start=source_location,
            suffix='.html',
            index_file_name='' if self.hide_index_html else 'index.html',
        )
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
        resources = self.output / page.document.config.web.resources_prefix
        return resources.relative_to(start.parent)

    async def add_custom_files(self, document: Document):
        fs: FileSystem = self.project.fs
        config: Config = document.config

        for filename in document.config.web.resources_force_copy:
            source_path = (document.config.paths.resources or document.config.paths.root) / filename
            target_path = RelativePath() / document.config.web.resources_prefix / filename
            self.waiter.add_task(self.add_file_from_project(source_path, target_path))

        for script in config.web.custom_scripts:
            source = RelativePath(script)
            assert source.suffix == '.js'
            target = RelativePath() / source.name
            await self.add_file_from_project(source, target)
            self.heads[document].append(HeadJsFile(target))

        for style in config.web.custom_styles:
            source = RelativePath(style)
            match source.suffix:
                case '.css':
                    target = RelativePath() / source.name
                    self.waiter.add_task(self.add_file_from_project(source, target))
                    self.heads[document].append(HeadCssFile(target))

                case '.sass' | '.scss':
                    source = fs.resolve(source)
                    target = RelativePath('_static') / f'{source.stem}.css'
                    sass = await self.compile_sass(source)
                    self.add_file_from_data(target, sass)
                    self.heads[document].append(HeadCssFile(target))

                case _:
                    raise ValueError(source)

    async def prepare_search_indexer(self, document: Document):
        config: Config = document.config
        if config.web.search.engine is None:
            return

        # Select the search indexer implementation
        indexer_class = {
            SearchIndexerName.PAGEFIND: PagefindIndexer,
        }[config.web.search.engine]

        # Select the index file path
        index_relative_path = None
        if config.web.search.index_path is not None:
            index_relative_path = expand_vars(config.web.search.index_path,
                                              lang=document.lang, codename=document.codename)

        # Initialize the indexer
        indexer = indexer_class(self, document, index_relative_path)
        await indexer.initialize()
        self._indexers[document] = indexer

        # Put required files to the HTML head
        self.heads[document] += indexer.head_tags()

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


class WebProcessor(AbstractHtmlProcessor[WebBuilder]):
    @override
    @lru_cache
    def get_highlighter(self, document: Document) -> Highlighter:
        config: Config = document.config
        match config.web.highlight:
            case Config_HighlightJS() as config_highlightjs:
                return HighlightJs(config_highlightjs, self.builder)
            case Config_Prism() as config_prism:
                return Prism(config_prism, self.builder)
            case Config_Pygments() as config_pygments:
                return Pygments(config_pygments, self.builder)


@final
class WebTheme(AbstractHtmlTheme):
    TYPE = 'web'
