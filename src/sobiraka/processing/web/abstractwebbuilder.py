from __future__ import annotations

import re
from abc import ABCMeta, abstractmethod
from asyncio import Task, TaskGroup, create_subprocess_exec, create_task
from copy import deepcopy
from subprocess import PIPE
from typing import final

from panflute import Image

from sobiraka.models import Page, Volume
from sobiraka.models.config import Config
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath, panflute_to_bytes
from .head import Head
from ..abstract import Processor
from ..plugin import WebTheme


class AbstractWebBuilder(Processor, metaclass=ABCMeta):

    def __init__(self):
        Processor.__init__(self)

        self._html_builder_tasks: list[Task] = []
        self._results: set[AbsolutePath] = set()
        self._head: Head = Head()

    @final
    async def add_additional_static_files(self, volume: Volume):
        async with TaskGroup() as tg:
            for filename in volume.config.html.resources_force_copy:
                source_path = (volume.config.paths.resources or volume.config.paths.root) / filename
                target_path = volume.config.html.resources_prefix / filename
                tg.create_task(self.add_file_from_project(source_path, target_path))

    @final
    async def compile_all_sass(self, theme: WebTheme):
        async with TaskGroup() as tg:
            for source_path, target_path in theme.sass_files.items():
                source_path = theme.theme_dir / source_path
                target_path = RelativePath('_static') / target_path
                tg.create_task(self.compile_sass(source_path, target_path))

    async def process4(self, page: Page):
        self.apply_postponed_image_changes(page)
        html = await self.render_html(page)
        RT[page].bytes = html

    @final
    def apply_postponed_image_changes(self, page: Page):
        for image, new_url in RT[page].converted_image_urls:
            image.url = new_url
        for image, link in RT[page].links_that_follow_images:
            link.url = image.url

    @final
    async def render_html(self, page: Page) -> bytes:
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

        return html

    @classmethod
    def expand_path_vars(cls, text: str, volume: Volume) -> str:
        def _substitution(m: re.Match) -> str:
            return {
                '$LANG': volume.lang or '',
                '$VOLUME': volume.codename or 'all',
                '$AUTOPREFIX': volume.autoprefix,
            }[m.group()]

        return re.sub(r'\$\w+', _substitution, text)

    @abstractmethod
    def get_root_prefix(self, page: Page) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_path_to_static(self, page: Page) -> RelativePath:
        raise NotImplementedError

    @abstractmethod
    def get_path_to_resources(self, page: Page) -> RelativePath:
        raise NotImplementedError

    async def process_image(self, image: Image, page: Page) -> tuple[Image, ...]:
        config: Config = page.volume.config

        # Run the default processing
        # It is important to run it first, since it normalizes the path
        image, = await super().process_image(image, page)
        assert isinstance(image, Image)
        if image.url is None:
            return image,

        # Schedule copying the image file to the output directory
        source_path = config.paths.resources / image.url
        target_path = RelativePath(config.html.resources_prefix) / image.url
        if target_path not in self._html_builder_tasks:
            self._html_builder_tasks.append(create_task(self.add_file_from_project(source_path, target_path)))

        # Use the path relative to the page path
        # (we postpone the actual change in the element to not confuse the WebTheme custom code later)
        new_url = self.get_relative_image_url(image, page)
        if new_url != image.url:
            RT[page].converted_image_urls.append((image, new_url))

        return image,

    @abstractmethod
    def get_relative_image_url(self, image: Image, page: Page) -> str:
        raise NotImplementedError

    ################################################################################
    # Functions used for additional tasks

    @abstractmethod
    async def add_file_from_location(self, source: AbsolutePath, target: RelativePath):
        raise NotImplementedError

    @final
    async def add_directory_from_location(self, source: AbsolutePath, target: RelativePath):
        async with TaskGroup() as tg:
            for file_source in source.glob('**/*'):
                if file_source.is_file():
                    file_target = target / file_source.relative_to(source)
                    tg.create_task(self.add_file_from_location(file_source, file_target))

    @abstractmethod
    async def add_file_from_project(self, source: RelativePath, target: RelativePath):
        raise NotImplementedError

    @abstractmethod
    async def compile_sass(self, source: AbsolutePath, destination: RelativePath):
        raise NotImplementedError
