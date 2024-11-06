import re
from abc import ABCMeta
from collections import defaultdict
from contextlib import suppress
from os.path import normpath
from typing import Generic, TYPE_CHECKING, TypeVar
from typing_extensions import override

from panflute import Code, Element, Header, Image, Link, Para, Space, Str, Table, stringify

from sobiraka.models import Anchor, BadImage, BadLink, DirPage, FileSystem, Page, PageHref, PageStatus, UrlHref, Volume
from sobiraka.models.config import Config
from sobiraka.models.exceptions import DisableLink
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, PathGoesOutsideStartDirectory, RelativePath, absolute_or_relative
from .dispatcher import Dispatcher
from ..directive import Directive

if TYPE_CHECKING:
    pass

B = TypeVar('B', bound='Builder')


class Processor(Dispatcher, Generic[B], metaclass=ABCMeta):

    def __init__(self, builder: B):
        super().__init__()
        self.builder: B = builder
        self.directives: dict[Page, list[Directive]] = defaultdict(list)

    async def process_role_doc(self, code: Code, page: Page):
        if m := re.fullmatch(r'(.+) < (.+) >', code.text, flags=re.X):
            label = m.group(1).strip()
            target_text = m.group(2)
        else:
            label = None
            target_text = code.text

        link = Link(Str(label))
        await self.process_internal_link(link, target_text, page)
        return (link,)

    @override
    async def process_directive(self, directive: Directive, page: Page) -> tuple[Element, ...]:
        self.directives[page].append(directive)
        return await super().process_directive(directive, page)

    @override
    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        if header.level == 1:
            # Use the top level header as the page title
            RT[page].title = stringify(header)

            # Maybe skip numeration for the whole page
            if 'unnumbered' in header.classes:
                RT[page].skip_numeration = True

        else:
            # Generate anchor identifier if not provided
            identifier = header.identifier
            if not identifier:
                identifier = stringify(header)
                identifier = identifier.lower()
                identifier = re.sub(r'\W+', '-', identifier)

            # Remember the anchor
            anchor = Anchor(header, identifier, label=stringify(header), level=header.level)
            RT[page].anchors.append(anchor)

            # Maybe skip numeration for the section
            if 'unnumbered' in header.classes:
                RT[anchor].skip_numeration = True

        return header,

    @override
    async def process_image(self, image: Image, page: Page) -> tuple[Element, ...]:
        """
        Get the image path, process variables inside it, and make it relative to the resources directory.

        If the file does not exist, create an Issue and set `image.url` to None.
        """
        volume: Volume = page.volume
        config: Config = volume.config
        fs: FileSystem = volume.project.fs

        path = image.url.replace('$LANG', volume.lang or '')
        path = absolute_or_relative(path)
        if isinstance(path, AbsolutePath):
            path = path.relative_to('/')
        else:
            path = page.path_in_project.parent / path
            path = RelativePath(normpath(path))
            path = path.relative_to(volume.config.paths.resources)

        if fs.exists(config.paths.resources / path):
            image.url = str(path)
        else:
            RT[page].issues.append(BadImage(image.url))
            image.url = None

        return (image,)

    @override
    async def process_link(self, link: Link, page: Page):
        if re.match(r'^\w+:', link.url):
            RT[page].links.append(UrlHref(link.url))
        else:
            if page.path_in_volume.suffix == '.rst':
                RT[page].issues.append(BadLink(link.url))
                return
            await self.process_internal_link(link, link.url, page)

    @override
    async def process_para(self, para: Para, page: Page) -> tuple[Element, ...]:
        para, = await super().process_para(para, page)
        assert isinstance(para, Para)

        with suppress(AssertionError):
            assert len(para.content) >= 1
            assert isinstance(para.content[0], Str)
            assert para.content[0].text.startswith('//')

            text = ''
            for elem in para.content:
                assert isinstance(elem, (Str, Space))
                text += stringify(elem)

            if m := re.fullmatch(r'// table-id: (\S+)', text):
                table_id = m.group(1)
                table = para.next
                if not isinstance(table, Table):
                    raise RuntimeError(f'Wait, where is the table? [{table_id}]')
                RT.IDS[id(table)] = table_id
                return ()

        return (para,)

    # region Process links

    async def process_internal_link(self, elem: Link, target_text: str, page: Page):
        try:
            m = re.fullmatch(r'(?: \$ ([A-z0-9\-_]+)? )? (/)? ([^#]+)? (?: [#] (.+) )?$', target_text, re.VERBOSE)
            volume_name, is_absolute, target_path_str, target_anchor = m.groups()

            if (volume_name, is_absolute, target_path_str) == (None, None, None):
                target = page

            else:
                volume = page.volume
                if volume_name is not None:
                    volume = page.volume.project.get_volume(volume_name)
                    is_absolute = True

                target_path = RelativePath(target_path_str or '.')
                if not is_absolute:
                    if isinstance(page, DirPage):
                        target_path = (page.path_in_volume / target_path).resolve()
                    else:
                        target_path = RelativePath(normpath(page.path_in_volume.parent / target_path))

                target = volume.pages_by_path[target_path]

            href = PageHref(target, target_anchor)
            RT[page].links.append(href)
            RT[page].dependencies.add(href.target)
            self.builder.schedule_for_stage2(page, self.process2_internal_link(elem, href, target_text, page))

        except (KeyError, ValueError, PathGoesOutsideStartDirectory):
            RT[page].issues.append(BadLink(target_text))

    async def process2_internal_link(self, elem: Link, href: PageHref, target_text: str, page: Page):
        await self.builder.require(href.target, PageStatus.PROCESS1)

        if href.anchor:
            try:
                anchor = RT[href.target].anchors.by_identifier(href.anchor)
                if not elem.content:
                    elem.content = Str(anchor.label),

            except (KeyError, AssertionError):
                RT[page].issues.append(BadLink(target_text))
                return

        try:
            elem.url = self.builder.make_internal_url(href, page=page)
            if not elem.content:
                elem.content = Str(RT[href.target].title),

        except DisableLink:
            i = elem.parent.content.index(elem)
            elem.parent.content[i:i + 1] = elem.content
            return

    # endregion
